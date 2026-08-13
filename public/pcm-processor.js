class PCMProcessor extends AudioWorkletProcessor {
  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (input && input.length > 0) {
      const channel = input[0];
      if (channel && channel.length > 0) {
        // Send Float32 PCM samples from AudioWorklet thread to main thread
        this.port.postMessage(channel);
      }
    }
    return true;
  }
}

registerProcessor("pcm-processor", PCMProcessor);
