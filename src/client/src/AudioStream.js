import React, { useState, useEffect, useRef } from 'react';
import io from 'socket.io-client';

const AudioStream = () => {
  const [audioContext, setAudioContext] = useState(null);
  const [buttonClicked, setButtonClicked] = useState(false);
  const [audioNode, setAudioNode] = useState(null);

  const [mediaStream, setMediaStream] = useState(null);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const mediaBuffer = useRef([]);

  const socketRef = useRef(null);

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

    const startRecording = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        setMediaStream(stream);

        const options = { mimeType: "audio/webm" };
        const recorder = new MediaRecorder(stream, options);

        recorder.ondataavailable = (event) => {

          if (event.data.size > 0 && socketRef.current) {
            const reader = new FileReader();

            reader.onload = () => {
              const arrayBuffer = reader.result;
              mediaBuffer.current.push(arrayBuffer);

              const totalLength = mediaBuffer.current.reduce((acc, buf) => acc + buf.byteLength, 0);
              const processLength = totalLength - (totalLength % 4); // Ensure length is multiple of 4

              if (processLength > 0) {
                const combinedBuffer = new Uint8Array(processLength);
                let offset = 0;
                let remainingBuffer = [];

                for (const buf of mediaBuffer.current) {
                  if (offset + buf.byteLength <= processLength) {
                    combinedBuffer.set(new Uint8Array(buf), offset);
                    offset += buf.byteLength;
                  } else {
                    const remainingBytes = processLength - offset;
                    combinedBuffer.set(new Uint8Array(buf.slice(0, remainingBytes)), offset);
                    remainingBuffer.push(buf.slice(remainingBytes));
                    offset += remainingBytes;
                    break;
                  }
                }

                mediaBuffer.current = remainingBuffer;  // Keep remaining bytes in buffer

                try {
                  const float32Array = new Float32Array(combinedBuffer.buffer);
                  socketRef.current.emit('audio_input', float32Array);
                } catch (error) {
                  console.error('Failed to convert ArrayBuffer to Float32Array:', error);
                }
              }
            };

            reader.onerror = (error) => {
              console.error('Error reading Blob as ArrayBuffer:', error);
            };

            reader.readAsArrayBuffer(event.data);
          }

        };

        recorder.onerror = (event) => {
          console.error('Recorder error:', event.error);
        };

        // Send chunks every 100ms
        recorder.start(100);
        setMediaRecorder(recorder);
      } catch (error) {
        console.error('Error accessing microphone:', error);
      }
    };

    const stopRecording = () => {
      if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        setMediaRecorder(null);
        setMediaStream(null);
      }
    };

    if (buttonClicked) {
      console.log("Opening audio context.");
      initAudioContext();
      console.log("Opening audio socket.");
      const newSocket = io('ws://localhost:5000');
      socketRef.current = newSocket;
      startRecording();
    } else {
      if (audioContext) {
        console.log("Closing audio context.");
        audioContext.close();
        setAudioContext(null);
      }
      if (socketRef.current) {
        console.log("Closing socket.");
        socketRef.current.close();
        socketRef.current = null;
      }
      stopRecording();
      setAudioNode(null);
    }

    return () => {
      if (audioContext && audioContext.state !== 'closed') {
        console.log("Closing audio context.");
        audioContext.close();
      }
      if (socketRef.current && socketRef.current.connected === true) {
        console.log("Closing socket.");
        socketRef.current.close();
      }
      stopRecording();
    };
  }, [buttonClicked]);

  useEffect(() => {
    if (audioNode && socketRef.current) {
      const handleAudioData = (data) => {
        const float32Array = new Float32Array(data);
        audioNode.port.postMessage({ message: 'audioData', audioData: float32Array });
      };

      socketRef.current.on('audio', handleAudioData);

      return () => {
        if(socketRef.current) {
          socketRef.current.off('audio');
        }
      };
    }
  }, [audioNode]);

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
