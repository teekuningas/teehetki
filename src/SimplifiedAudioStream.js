import React, { useEffect } from 'react';
import io from 'socket.io-client';

const AudioStream = () => {
  useEffect(() => {
    // Connect to the WebSocket server
    const socket = io.connect('ws://localhost:5000');

    // Handle the connect event
    socket.on('connect', () => {
      console.log('Connected to server');
    });

    // Handle the disconnect event
    socket.on('disconnect', () => {
      console.log('Disconnected from server');
    });

    // Handle custom messages from the server
    socket.on('message', (data) => {
      console.log('Received message from server:', data);  // Debug
    });

    // Clean up the connection on component unmount
    return () => {
      socket.disconnect();
    };
  }, []);

  return (
    <div>
      <h1>Audio Stream</h1>
    </div>
  );
};

export default AudioStream;
