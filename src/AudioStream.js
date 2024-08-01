import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';

console.log("Trying to connect!");
const socket = io('ws://localhost:5000');
console.log("Connected!");

const AudioStream = () => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [audioContext, setAudioContext] = useState(null);
  const [mediaStream, setMediaStream] = useState(null);
  const [audioSource, setAudioSource] = useState(null);
  const [audioProcessor, setAudioProcessor] = useState(null);
  const [audioQueue, setAudioQueue] = useState([]);

  useEffect(() => {
    socket.on('audio', (audioData) => {
      console.log('Received audio data:', audioData);  // Debug
      if (audioContext) {
        const float32Array = new Float32Array(audioData);
        setAudioQueue(prevQueue => [...prevQueue, float32Array]);
      }
    });

    return () => {
      socket.off('audio');
    };
  }, [audioContext]);

  useEffect(() => {
    if (audioContext && audioQueue.length > 0) {
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      processor.onaudioprocess = (e) => {
        if (audioQueue.length > 0) {
          const outputBuffer = e.outputBuffer.getChannelData(0);
          const inputBuffer = audioQueue.shift();
          outputBuffer.set(inputBuffer);
        }
      };
      processor.connect(audioContext.destination);
      setAudioProcessor(processor);
    }

    return () => {
      if (audioProcessor) {
        audioProcessor.disconnect();
      }
    };
  }, [audioContext, audioQueue]);

  const startStreaming = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const context = new AudioContext();
      await context.resume(); // Ensure the AudioContext is running
      const source = context.createMediaStreamSource(stream);

      const processor = context.createScriptProcessor(4096, 1, 1);
      processor.onaudioprocess = (e) => {
        const audioData = e.inputBuffer.getChannelData(0);
        const audioArray = Array.from(audioData);
        socket.emit('audio', audioArray);
      };

      source.connect(processor);
      processor.connect(context.destination);

      setAudioContext(context);
      setMediaStream(stream);
      setAudioSource(source);
      setAudioProcessor(processor);
      setIsStreaming(true);
    } catch (error) {
      console.error('Error accessing media devices.', error);
    }
  };

  const stopStreaming = () => {
    if (mediaStream) {
      mediaStream.getTracks().forEach(track => track.stop());
    }
    if (audioSource) {
      audioSource.disconnect();
    }
    if (audioProcessor) {
      audioProcessor.disconnect();
    }
    if (audioContext) {
      audioContext.close();
    }
    setAudioContext(null);
    setMediaStream(null);
    setAudioSource(null);
    setAudioProcessor(null);
    setIsStreaming(false);
  };

  return (
    <div>
      <button onClick={isStreaming ? stopStreaming : startStreaming}>
        {isStreaming ? 'Stop' : 'Start'} Streaming
      </button>
    </div>
  );
};

export default AudioStream;
