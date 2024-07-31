import React, { useState, useEffect } from 'react';
import SimplePeer from 'simple-peer';
import io from 'socket.io-client';

const socket = io('ws://localhost:5000');

const AudioStream = () => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [peer, setPeer] = useState(null);
  const [audio, setAudio] = useState(null);

  const startStreaming = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const p = new SimplePeer({ initiator: true, stream });

      const handleSignal = (data) => {
        p.signal(data);
      };

      p.on('signal', (data) => {
        socket.emit('signal', data);
      });

      p.on('stream', (stream) => {
        const audioElement = new Audio();
        audioElement.srcObject = stream;
        audioElement.play();
        setAudio(audioElement);
      });

      p.on('iceconnectionstatechange', () => {
        console.log('ICE Connection State:', p.iceConnectionState);
      });

      socket.on('signal', handleSignal);

      p.on('close', () => {
        socket.off('signal', handleSignal);
        if (audio) {
          audio.pause();
          setAudio(null);
        }
      });

      setPeer(p);
      setIsStreaming(true);
    } catch (error) {
      console.error('Error accessing media devices.', error);
    }
  };

  const stopStreaming = () => {
    if (peer) {
      peer.destroy();
      setPeer(null);
    }
    if (audio) {
      audio.pause();
      setAudio(null);
    }
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
