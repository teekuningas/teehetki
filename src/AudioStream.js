import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';

const socket = io('ws://localhost:5000');

const AudioStream = () => {
  const [audioContext, setAudioContext] = useState(null);
  const [audioNode, setAudioNode] = useState(null);

  useEffect(() => {
    const initAudioContext = async () => {
      const audioContext = new AudioContext({sampleRate: 8000});
      setAudioContext(audioContext);
      await audioContext.audioWorklet.addModule('./processor.js');
      const audioNode = new AudioWorkletNode(audioContext, 'audio-processor');
      audioNode.connect(audioContext.destination);
      setAudioNode(audioNode);
    };

    initAudioContext();

    return () => {
      if (audioContext) {
        audioContext.close();
      }
      socket.off('audio');
    };
  }, []);

  useEffect(() => {
    if (audioNode) {
      socket.on('audio', (data) => {
        const float32Array = new Float32Array(data);
        audioNode.port.postMessage({ message: 'audioData', audioData: float32Array });
      });

      return () => {
        socket.off('audio');
      };
    }
  }, [audioNode]);

  return (
    <div>
      <p> Hello there tea party</p>
    </div>
  );
};

export default AudioStream;
