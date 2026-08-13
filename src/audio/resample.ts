export function resampleTo16k(input: Float32Array, inputSampleRate: number): Float32Array {
  const targetRate = 16000;

  if (inputSampleRate === targetRate) {
    return input;
  }

  const ratio = inputSampleRate / targetRate;
  const outputLength = Math.round(input.length / ratio);
  const output = new Float32Array(outputLength);

  for (let i = 0; i < outputLength; i++) {
    const position = i * ratio;
    const index = Math.floor(position);
    const nextIndex = Math.min(index + 1, input.length - 1);
    const fraction = position - index;

    output[i] = input[index] * (1 - fraction) + input[nextIndex] * fraction;
  }

  return output;
}
