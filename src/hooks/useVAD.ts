import { useRef, useState, useCallback } from 'react';

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

  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const animationRef = useRef<number | null>(null);
  
  const [isVoiceDetected, setIsVoiceDetected] = useState<boolean>(false);
  const [audioLevel, setAudioLevel] = useState<number>(0);

  const stopMonitoring = useCallback(() => {
    if (animationRef.current !== null) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }

    if (audioContextRef.current) {
      if (audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close().catch(() => {});
      }
      audioContextRef.current = null;
    }

    analyserRef.current = null;
    sourceRef.current = null;
    setIsVoiceDetected(false);
    setAudioLevel(0);
  }, []);

  const startMonitoring = useCallback(
    (
      stream: MediaStream,
      onSpeechStart: () => void,
      onSilence: () => void
    ) => {
      // Clean up any existing monitoring session first
      stopMonitoring();

      try {
        const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
        const audioContext = new AudioContextClass();
        const analyser = audioContext.createAnalyser();
        analyser.fftSize = 2048;

        const source = audioContext.createMediaStreamSource(stream);
        source.connect(analyser);

        audioContextRef.current = audioContext;
        analyserRef.current = analyser;
        sourceRef.current = source;

        const data = new Uint8Array(analyser.fftSize);

        let speaking = false;
        let silenceStart: number | null = null;
        let speechStartAt: number | null = null;

        const monitor = () => {
          if (!analyserRef.current) return;

          analyserRef.current.getByteTimeDomainData(data);

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
            } else if (Date.now() - silenceStart >= silenceDelay) {
              const totalSpeechTime = speechStartAt ? Date.now() - speechStartAt : 0;
              speaking = false;
              setIsVoiceDetected(false);

              if (totalSpeechTime >= minSpeechTime) {
                onSilence();
                stopMonitoring();
                return;
              } else {
                // Speech was too brief (cough/noise), reset silence
                silenceStart = null;
              }
            }
          }

          animationRef.current = requestAnimationFrame(monitor);
        };

        monitor();
      } catch (err) {
        console.warn('Web Audio VAD monitoring notice:', err);
      }
    },
    [stopMonitoring, threshold, silenceDelay, minSpeechTime]
  );

  return {
    isVoiceDetected,
    audioLevel,
    startMonitoring,
    stopMonitoring,
  };
}
