import React, { useState, useEffect } from 'react';
import SimplePeer from 'simple-peer';
import io from 'socket.io-client';

const socket = io('ws://localhost:5000');

const Transcription = () => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [transcription, setTranscription] = useState('');
  const [peer, setPeer] = useState(null);

  useEffect(() => {
    socket.on('transcription', (data) => {
      setTranscription((prev) => prev + ' ' + data);
    });

    return () => {
      socket.off('transcription');
    };
  }, []);

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

      p.on('iceConnectionStateChange', () => {
        console.log('ICE Connection State:', p.iceConnectionState);
      });

      socket.on('signal', handleSignal);

      p.on('close', () => {
        socket.off('signal', handleSignal);
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
    setIsStreaming(false);
  };

  return (
    <div>
      <button onClick={isStreaming ? stopStreaming : startStreaming}>
        {isStreaming ? 'Stop' : 'Start'} Streaming
      </button>
      <div>
        <h3>Transcription:</h3>
        <p>{transcription}</p>
      </div>
    </div>
  );
};

export default Transcription;
