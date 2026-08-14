import { resampleTo16k } from './resample';

export class PCMStreamer {
  private websocket: WebSocket;
  private audioContext: AudioContext | null = null;
  private source: MediaStreamAudioSourceNode | null = null;
  private processor: ScriptProcessorNode | null = null;
  private stream: MediaStream | null = null;

  constructor(websocket: WebSocket) {
    this.websocket = websocket;
  }

  async start(existingStream?: MediaStream): Promise<void> {
    if (existingStream) {
      this.stream = existingStream;
    } else {
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
    }

    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
    this.audioContext = new AudioContextClass();
    
    console.log('PCMStreamer: AudioContext native sample rate:', this.audioContext.sampleRate);

    this.source = this.audioContext.createMediaStreamSource(this.stream);

    // Use 4096 buffer size, 1 input channel, 1 output channel
    this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);

    this.processor.onaudioprocess = (event: AudioProcessingEvent) => {
      if (!this.audioContext) return;

      const input = event.inputBuffer.getChannelData(0);
      const resampled = resampleTo16k(input, this.audioContext.sampleRate);
      const pcm16 = this.floatTo16BitPCM(resampled);

      if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
        this.websocket.send(pcm16);
      }
    };

    this.source.connect(this.processor);
    // Connect processor through a zero-gain node to keep ScriptProcessor running without routing mic to speakers
    const muteGain = this.audioContext.createGain();
    muteGain.gain.value = 0;
    this.processor.connect(muteGain);
    muteGain.connect(this.audioContext.destination);
  }

  private floatTo16BitPCM(float32Array: Float32Array): ArrayBuffer {
    const buffer = new ArrayBuffer(float32Array.length * 2);
    const view = new DataView(buffer);

    for (let i = 0; i < float32Array.length; i++) {
      let sample = Math.max(-1, Math.min(1, float32Array[i]));
      sample = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
      view.setInt16(i * 2, sample, true); // Little endian
    }

    return buffer;
  }

  stop(): void {
    if (this.processor) {
      this.processor.disconnect();
      this.processor.onaudioprocess = null;
      this.processor = null;
    }

    if (this.source) {
      this.source.disconnect();
      this.source = null;
    }

    if (this.audioContext) {
      if (this.audioContext.state !== 'closed') {
        this.audioContext.close().catch(() => {});
      }
      this.audioContext = null;
    }

    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
      this.stream = null;
    }
  }
}
