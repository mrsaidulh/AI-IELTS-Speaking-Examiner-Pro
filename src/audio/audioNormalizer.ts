/**
 * Dynamic Automatic Gain Normalizer using Web Audio API DynamicsCompressor & GainNode
 * Normalizes uneven microphone inputs across low-gain headsets, quiet internal laptop mics,
 * and high-gain studio microphones without distortion or harsh digital clipping.
 */

export interface NormalizedAudioPipeline {
  audioContext: AudioContext;
  sourceNode: MediaStreamAudioSourceNode;
  gainNode: GainNode;
  compressorNode: DynamicsCompressorNode;
  analyserNode: AnalyserNode;
  destinationNode: MediaStreamAudioDestinationNode;
  normalizedStream: MediaStream;
  setGain: (gainMultiplier: number) => void;
  cleanup: () => void;
}

export function createNormalizedAudioPipeline(
  inputStream: MediaStream,
  targetDb: number = -16
): NormalizedAudioPipeline {
  const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
  const audioContext = new AudioContextClass();

  const sourceNode = audioContext.createMediaStreamSource(inputStream);

  // 1. High-Pass Filter: Cut sub-audible rumble, desk thumps, and low-frequency electrical hum (< 80Hz)
  const highPassFilter = audioContext.createBiquadFilter();
  highPassFilter.type = 'highpass';
  highPassFilter.frequency.value = 80;
  highPassFilter.Q.value = 0.707;

  // 2. Dynamics Compressor: Smooth out dynamic spikes (laughter, loud exclamations) while boosting quiet whispers
  const compressorNode = audioContext.createDynamicsCompressor();
  compressorNode.threshold.setValueAtTime(-24, audioContext.currentTime); // dB
  compressorNode.knee.setValueAtTime(10, audioContext.currentTime); // smooth soft-knee curve
  compressorNode.ratio.setValueAtTime(4, audioContext.currentTime); // 4:1 broadcast compression ratio
  compressorNode.attack.setValueAtTime(0.003, audioContext.currentTime); // 3ms ultra-fast attack
  compressorNode.release.setValueAtTime(0.25, audioContext.currentTime); // 250ms natural speech release

  // 3. Make-up Gain Node: Normalizes average spoken level to optimal broadcast/STT loudness
  const gainNode = audioContext.createGain();
  gainNode.gain.setValueAtTime(1.6, audioContext.currentTime); // +4.1 dB optimal speech lift

  // 4. Low-Pass Filter: Remove ultra-high frequency hiss (> 8500Hz) above vocal articulation
  const lowPassFilter = audioContext.createBiquadFilter();
  lowPassFilter.type = 'lowpass';
  lowPassFilter.frequency.value = 8500;
  lowPassFilter.Q.value = 0.707;

  // 5. Analyser Node: Extract normalized signal for visualizer and VAD
  const analyserNode = audioContext.createAnalyser();
  analyserNode.fftSize = 1024;
  analyserNode.smoothingTimeConstant = 0.8;

  // 6. Destination Node: Outputs a clean, normalized MediaStream to feed MediaRecorder and PCM streamer
  const destinationNode = audioContext.createMediaStreamDestination();

  // Audio Graph Flow:
  // inputStream -> HighPass (80Hz) -> Compressor -> Gain -> LowPass (8.5kHz) -> [Analyser & Stream Destination]
  sourceNode.connect(highPassFilter);
  highPassFilter.connect(compressorNode);
  compressorNode.connect(gainNode);
  gainNode.connect(lowPassFilter);
  
  lowPassFilter.connect(analyserNode);
  lowPassFilter.connect(destinationNode);

  // Dynamic automatic leveling loop based on RMS monitoring
  let autoLevelAnim: number | null = null;
  const buffer = new Float32Array(analyserNode.fftSize);

  let currentAutoGain = 1.6;
  const updateAutoGain = () => {
    if (audioContext.state === 'closed') return;

    analyserNode.getFloatTimeDomainData(buffer);
    let sum = 0;
    for (let i = 0; i < buffer.length; i++) {
      sum += buffer[i] * buffer[i];
    }
    const rms = Math.sqrt(sum / buffer.length);

    // If signal is active speech (above background floor)
    if (rms > 0.015) {
      const currentDb = 20 * Math.log10(rms);
      const dbDiff = targetDb - currentDb; // Target difference

      // Clamp gain adjustment between 0.6x and 3.5x (+/- ~10dB)
      const targetGain = Math.max(0.6, Math.min(3.5, Math.pow(10, dbDiff / 40)));
      
      // Smooth exponentially to prevent pumping
      currentAutoGain += (targetGain - currentAutoGain) * 0.05;
      gainNode.gain.setTargetAtTime(currentAutoGain, audioContext.currentTime, 0.08);
    }

    autoLevelAnim = requestAnimationFrame(updateAutoGain);
  };

  updateAutoGain();

  const setGain = (gainMultiplier: number) => {
    gainNode.gain.setValueAtTime(gainMultiplier, audioContext.currentTime);
  };

  const cleanup = () => {
    if (autoLevelAnim !== null) {
      cancelAnimationFrame(autoLevelAnim);
      autoLevelAnim = null;
    }
    try {
      sourceNode.disconnect();
      highPassFilter.disconnect();
      compressorNode.disconnect();
      gainNode.disconnect();
      lowPassFilter.disconnect();
      analyserNode.disconnect();
      destinationNode.disconnect();
      if (audioContext.state !== 'closed') {
        audioContext.close().catch(() => {});
      }
    } catch (e) {
      // safe cleanup
    }
  };

  return {
    audioContext,
    sourceNode,
    gainNode,
    compressorNode,
    analyserNode,
    destinationNode,
    normalizedStream: destinationNode.stream,
    setGain,
    cleanup,
  };
}
