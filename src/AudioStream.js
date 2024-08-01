import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';

const socket = io('ws://localhost:5000');

const AudioStream = () => {
  const [audioContext, setAudioContext] = useState(null);

  useEffect(() => {
    const audioContext = new AudioContext();
    setAudioContext(audioContext);

    socket.on('audio', async (audioData) => {
      if (audioContext) {
        const float32Array = new Float32Array(audioData);
        playAudio(audioContext, float32Array);
      }
    });

    return () => {                                                                                           if (audioContext) {                                                                                      audioContext.close();                                                                                }
      socket.off('audio');
    };

  }, []);


  const playAudio = (audioContext, audioData) => {
    const audioBuffer = audioContext.createBuffer(1, audioData.length, 8000);
    audioBuffer.copyToChannel(audioData, 0);
    const player = audioContext.createBufferSource();
    player.buffer = audioBuffer;
    player.connect(audioContext.destination);
    player.start(0);
  };

  return (
    <div>
      <p> Hello there tea party</p>
    </div>
  );
};

export default AudioStream;
