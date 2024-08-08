import React, { useState, useEffect, useRef } from 'react';
import './styles.css';
import io from 'socket.io-client';

const AudioStream = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [audioNode, setAudioNode] = useState(null);
  const [micNode, setMicNode] = useState(null);
  const [analyserNode, setAnalyserNode] = useState(null);
  const [threshold, setThreshold] = useState(0.001);

  const audioContextRef = useRef(null);
  const socketRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const canvasRef = useRef(null);

  const sampleRate = 8000;

  useEffect(() => {
    const initAudioContext = async () => {
      const audioContext = new AudioContext({ sampleRate: sampleRate });
      audioContextRef.current = audioContext;

      await audioContext.audioWorklet.addModule('./processor.js');
      const audioNode = new AudioWorkletNode(audioContext, 'audio-processor');
      audioNode.connect(audioContext.destination);
      setAudioNode(audioNode);

      await audioContext.audioWorklet.addModule('./micProcessor.js');
      const micNode = new AudioWorkletNode(audioContext, 'mic-processor');
      setMicNode(micNode);

      const analyserNode = audioContext.createAnalyser();
      analyserNode.fftSize = 256;
      setAnalyserNode(analyserNode);

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      const source = audioContext.createMediaStreamSource(stream);
      source.connect(micNode);
      source.connect(analyserNode);
    };

    if (isOpen) {
      console.log("Opening audio context.");
      initAudioContext();
      console.log("Opening socket.");
      const newSocket = io('ws://localhost:5000');
      socketRef.current = newSocket;

      // Send initial threshold value to the server
      newSocket.emit('threshold_update', threshold);
    } else {
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        console.log("Closing audio context.");
        audioContextRef.current.close();
        audioContextRef.current = null;
      }
      if (socketRef.current && socketRef.current.connected === true) {
        console.log("Closing socket.");
        socketRef.current.close();
        socketRef.current = null;
      }
      if(mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach(track => track.stop());
        mediaStreamRef.current = null;
      }
      setMicNode(null);
      setAudioNode(null);
      setAnalyserNode(null);
    }

    return () => {
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        console.log("Closing audio context.");
        audioContextRef.current.close();
      }
      if (socketRef.current && socketRef.current.connected === true) {
        console.log("Closing socket.");
        socketRef.current.close();
      }
    };
  }, [isOpen]);

  useEffect(() => {
    if (audioNode && socketRef.current) {
      const handleAudioData = (data) => {
        const float32Array = new Float32Array(data);
        audioNode.port.postMessage({ message: 'audioData', audioData: float32Array });
      };

      socketRef.current.on('audio', handleAudioData);

      return () => {
        if (socketRef.current) {
          socketRef.current.off('audio');
        }
      };
    }
  }, [audioNode]);

  useEffect(() => {
    if (micNode && socketRef.current) {
      // Handle audio data received from the micProcessor
      micNode.port.onmessage = (event) => {
        if (socketRef.current && socketRef.current.connected) {
          socketRef.current.emit('audio_input', event.data.audioData);
        }
      };
    }
  }, [micNode]);


  useEffect(() => {
    if (analyserNode) {
      const canvas = canvasRef.current;
      const canvasContext = canvas.getContext('2d');

      const renderFrame = () => {
        requestAnimationFrame(renderFrame);

        const bufferLength = analyserNode.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        analyserNode.getByteTimeDomainData(dataArray);

        canvasContext.clearRect(0, 0, canvas.width, canvas.height);

        let sumOfSquares = 0;
        for (let i = 0; i < bufferLength; i++) {
          const value = dataArray[i] - 128;
          sumOfSquares += value * value;
        }
        const rms = Math.sqrt(sumOfSquares / bufferLength);

        canvasContext.fillStyle = 'rgb(200, 200, 200)';
        canvasContext.fillRect(0, 0, canvas.width, canvas.height);

        const barWidth = (rms / 128) * canvas.width;

        canvasContext.fillStyle = 'rgb(0, 0, 0)';
        canvasContext.fillRect(0, 0, barWidth, canvas.height);
      };

      renderFrame();
    }
  }, [analyserNode]);

  const startButtonHandler = () => {
    setIsOpen(prevState => !prevState);
  };

  const thresholdHandler = () => {
    if (socketRef.current) {
      socketRef.current.emit('threshold_update', threshold);
    }
  };

  const handleThresholdChange = (event) => {
    setThreshold(parseFloat(event.target.value));
  };

  return (
    <div className="container">
      <div className="title">
        <h1>Teehetki</h1>
      </div>
      <div className="start-button">
        <button onClick={startButtonHandler}>
          {isOpen ? 'Stop' : 'Start'}
        </button>
      </div>
      <div className="threshold-slider">
        <label>VAD threshold:</label>
        <input
          type="range"
          min="0.0001"
          max="0.1"
          step="0.0001"
          value={threshold}
          onChange={handleThresholdChange}
        />
        <label>Value: {threshold}</label>
        <button onClick={thresholdHandler} disabled={!isOpen}>
          Set threshold
        </button>
      </div>
      <div className="canvas">
        <canvas ref={canvasRef}></canvas>
      </div>
    </div>
  );
};

export default AudioStream;
