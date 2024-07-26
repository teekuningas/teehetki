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
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const p = new SimplePeer({ initiator: true, stream });
    
    p.on('signal', (data) => {
      socket.emit('signal', data);
    });

    socket.on('signal', (data) => {
      p.signal(data);
    });

    setPeer(p);
    setIsStreaming(true);
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
