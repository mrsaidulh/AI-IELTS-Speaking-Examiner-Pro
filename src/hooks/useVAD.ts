import { useRef, useState, useCallback } from 'react';
import { createNormalizedAudioPipeline, NormalizedAudioPipeline } from '../audio/audioNormalizer';

export interface VADOptions {
  threshold?: number;         // RMS threshold for voice detection (default: 0.02)
  silenceDelay?: number;      // Silence timeout before stopping in ms (default: 1500ms)
  minSpeechTime?: number;     // Minimum required speech duration in ms (default: 300ms)
}

export function useVAD(options: VADOptions = {}) {
  const {
    threshold = 0.02,
    silenceDelay = 1500,
    minSpeechTime = 300,
  } = options;

  const pipelineRef = useRef<NormalizedAudioPipeline | null>(null);
  const animationRef = useRef<number | null>(null);
  
  const [isVoiceDetected, setIsVoiceDetected] = useState<boolean>(false);
  const [audioLevel, setAudioLevel] = useState<number>(0);
  const [analyserNode, setAnalyserNode] = useState<AnalyserNode | null>(null);
  const [normalizedStream, setNormalizedStream] = useState<MediaStream | null>(null);
  const [silenceProgress, setSilenceProgress] = useState<number>(0); // 0 (active) to 1 (full silence timeout)

  const stopMonitoring = useCallback(() => {
    if (animationRef.current !== null) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }

    if (pipelineRef.current) {
      pipelineRef.current.cleanup();
      pipelineRef.current = null;
    }

    setAnalyserNode(null);
    setNormalizedStream(null);
    setIsVoiceDetected(false);
    setAudioLevel(0);
    setSilenceProgress(0);
  }, []);

  const startMonitoring = useCallback(
    (
      rawStream: MediaStream,
      onSpeechStart: () => void,
      onSilence: () => void
    ): MediaStream => {
      // Clean up any existing monitoring session first
      stopMonitoring();

      try {
        // Initialize Web Audio API compressor & gain normalization pipeline
        const pipeline = createNormalizedAudioPipeline(rawStream);
        pipelineRef.current = pipeline;

        const analyser = pipeline.analyserNode;
        setAnalyserNode(analyser);
        setNormalizedStream(pipeline.normalizedStream);

        const data = new Uint8Array(analyser.fftSize);

        let speaking = false;
        let silenceStart: number | null = null;
        let speechStartAt: number | null = null;

        const monitor = () => {
          if (!pipelineRef.current) return;

          analyser.getByteTimeDomainData(data);

          let sum = 0;
          for (let i = 0; i < data.length; i++) {
            const value = (data[i] - 128) / 128;
            sum += value * value;
          }

          const rms = Math.sqrt(sum / data.length);
          setAudioLevel(Math.min(100, Math.round(rms * 500)));

          const voiceDetected = rms > threshold;
          setIsVoiceDetected(voiceDetected);

          if (voiceDetected) {
            setSilenceProgress(0);
            if (!speaking) {
              speaking = true;
              speechStartAt = Date.now();
              silenceStart = null;
              onSpeechStart();
            } else {
              silenceStart = null;
            }
          }

          if (speaking && !voiceDetected) {
            if (silenceStart === null) {
              silenceStart = Date.now();
              setSilenceProgress(0);
            } else {
              const elapsedSilence = Date.now() - silenceStart;
              setSilenceProgress(Math.min(1, elapsedSilence / silenceDelay));

              if (elapsedSilence >= silenceDelay) {
                const totalSpeechTime = speechStartAt ? Date.now() - speechStartAt : 0;
                speaking = false;
                setIsVoiceDetected(false);
                setSilenceProgress(1);

                if (totalSpeechTime >= minSpeechTime) {
                  onSilence();
                  stopMonitoring();
                  return;
                } else {
                  // Speech was too brief (cough/noise), reset silence
                  silenceStart = null;
                  setSilenceProgress(0);
                }
              }
            }
          }

          animationRef.current = requestAnimationFrame(monitor);
        };

        monitor();
        return pipeline.normalizedStream;
      } catch (err) {
        console.warn('Web Audio VAD & Normalizer notice:', err);
        return rawStream;
      }
    },
    [stopMonitoring, threshold, silenceDelay, minSpeechTime]
  );

  return {
    isVoiceDetected,
    audioLevel,
    analyserNode,
    normalizedStream,
    silenceProgress,
    startMonitoring,
    stopMonitoring,
  };
}
