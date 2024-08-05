import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';

const AudioStream = () => {
  const [audioContext, setAudioContext] = useState(null);
  const [buttonClicked, setButtonClicked] = useState(false);
  const [audioNode, setAudioNode] = useState(null);
  const [socket, setSocket] = useState(null);

  const sampleRate = 8000;

  useEffect(() => {
    const initAudioContext = async () => {
      const audioContext = new AudioContext({ sampleRate: sampleRate });
      setAudioContext(audioContext);
      await audioContext.audioWorklet.addModule('./processor.js');
      const audioNode = new AudioWorkletNode(audioContext, 'audio-processor');
      audioNode.connect(audioContext.destination);
      setAudioNode(audioNode);
    };

    if (buttonClicked) {
      console.log("Opening audio context.")
      initAudioContext();

      console.log("Opening audio socket.")
      const newSocket = io('ws://localhost:5000');
      setSocket(newSocket);

    } else {
      if (audioContext) {
        console.log("Closing audio context.")
        audioContext.close();
        setAudioContext(null);
      }
      if (socket) {
        console.log("Closing socket.")
        socket.close();
        setSocket(null);
      }
      setAudioNode(null);
    }

    return () => {
      if (audioContext && audioContext.state !== 'closed') {
        console.log("Closing audio context.")
        audioContext.close();
      }
      if (socket && socket.connected === true) {
        console.log("Closing socket.")
        socket.close();
      }
    };
  }, [buttonClicked]);

  useEffect(() => {
    if (audioNode && socket) {
      const handleAudioData = (data) => {
        const float32Array = new Float32Array(data);
        audioNode.port.postMessage({ message: 'audioData', audioData: float32Array });
      };

      socket.on('audio', handleAudioData);

      return () => {
        socket.off('audio');
      };
    }
  }, [audioNode, socket]);

  const buttonHandler = () => {
    setButtonClicked(prevState => !prevState);
  };

  return (
    <div>
      <p>Hello there tea party</p>
      <button onClick={buttonHandler}>
        {buttonClicked ? 'Stop' : 'Start'}
      </button>
    </div>
  );
};

export default AudioStream;
