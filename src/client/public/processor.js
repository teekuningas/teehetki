class AudioProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.buffer = new Float32Array();
    this.playbackStarted = false;
    this.sampleRate = 8000;
    this.highThreshold = this.sampleRate; // 1 second worth of samples
    this.lowThreshold = this.sampleRate / 2; // 0.5 second worth of samples

    // Receive audio data from the main thread, and add it to the buffer
    this.port.onmessage = (event) => {
      if (event.data.message === "audioData") {
        let newFetchedData = new Float32Array(
          this.buffer.length + event.data.audioData.length,
        );
        newFetchedData.set(this.buffer, 0);
        newFetchedData.set(event.data.audioData, this.buffer.length);
        this.buffer = newFetchedData;
      }
    };
  }

  // Take a chunk from the buffer and send it to the output to be played
  process(inputs, outputs, parameters) {
    const output = outputs[0];
    const channel = output[0];
    const bufferLength = this.buffer.length;

    if (this.playbackStarted) {
      // If getting samples in too low rate,
      // prefer larger breaks infrequently
      // over short breaks frequently.
      if (bufferLength < this.lowThreshold) {
        this.playbackStarted = false;
      } else {
        for (let i = 0; i < channel.length; i++) {
          channel[i] = i < bufferLength ? this.buffer[i] : 0;
        }
        this.buffer = this.buffer.slice(channel.length);
      }
    } else {
      if (bufferLength >= this.highThreshold) {
        this.playbackStarted = true;
      }
    }

    return true;
  }
}

registerProcessor("audio-processor", AudioProcessor);
