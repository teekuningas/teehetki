class MicProcessor extends AudioWorkletProcessor {
    process(inputs, outputs, parameters) {
        const input = inputs[0];
        if (input && input[0]) {
            const channelData = input[0];
            // Send the PCM data to the main thread
            this.port.postMessage({ audioData: channelData });
        }
        return true;
    }
}

registerProcessor('mic-processor', MicProcessor);
