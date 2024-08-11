import React, { useState, useEffect, useRef } from "react";
import "./styles.css";
import io from "socket.io-client";

function App() {
  // Should be the same as on server
  const sampleRate = 8000;

  const thresholdMin = 0.0001;
  const thresholdStep = 0.0001;
  const thresholdMax = 0.01;
  const thresholdInitial = 0.001;
  const systemPromptInitial =
    "Vastaa käyttäjälle lyhyesti kuin olisit puhelimessa.";

  const [isOpen, setIsOpen] = useState(false);
  const [audioNode, setAudioNode] = useState(null);
  const [micNode, setMicNode] = useState(null);
  const [analyserNode, setAnalyserNode] = useState(null);
  const [agentProcessing, setAgentProcessing] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);

  const [settings, setSettings] = useState({
    threshold: thresholdInitial,
    system_prompt: systemPromptInitial,
  });

  const audioContextRef = useRef(null);
  const socketRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const canvasRef = useRef(null);

  // Allow injecting api address at runtime
  // but default to localhost:5000
  const runtimeApiAddress = "%%RUNTIME_API_ADDRESS%%";
  const apiAddress = runtimeApiAddress.includes("RUNTIME_API_ADDRESS")
    ? "ws://localhost:5000"
    : runtimeApiAddress;

  useEffect(() => {
    const initAudioContext = async () => {
      // Initialize Audio API context
      const audioContext = new AudioContext({ sampleRate: sampleRate });
      audioContextRef.current = audioContext;

      // Add playback node
      await audioContext.audioWorklet.addModule("./processor.js");
      const audioNode = new AudioWorkletNode(audioContext, "audio-processor");
      audioNode.connect(audioContext.destination);
      setAudioNode(audioNode);

      // Set up source stream
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      const source = audioContext.createMediaStreamSource(stream);

      // Add mic node for getting socket-friendly output
      await audioContext.audioWorklet.addModule("./micProcessor.js");
      const micNode = new AudioWorkletNode(audioContext, "mic-processor");
      source.connect(micNode);
      setMicNode(micNode);

      // Add analyser node for trivial visualisations
      const analyserNode = audioContext.createAnalyser();
      analyserNode.fftSize = 256;
      source.connect(analyserNode);
      setAnalyserNode(analyserNode);
    };

    if (isOpen) {
      console.log("Opening audio context.");
      initAudioContext();

      console.log(`Opening socket to ${apiAddress}`);
      const newSocket = io(apiAddress);
      socketRef.current = newSocket;

      // Send initial setting values to the server
      newSocket.emit("settings_update", settings);

      // Listen for agent status
      newSocket.on("agent_status", (data) => {
        setAgentProcessing(data.is_processing);
        setChatHistory(data.chat_history);
      });
    } else {
      // Clean up context, source and nodes when requested

      if (
        audioContextRef.current &&
        audioContextRef.current.state !== "closed"
      ) {
        console.log("Closing audio context.");
        audioContextRef.current.close();
        audioContextRef.current = null;
      }

      if (socketRef.current && socketRef.current.connected === true) {
        console.log("Closing socket.");
        socketRef.current.close();
        socketRef.current = null;
      }

      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((track) => track.stop());
        mediaStreamRef.current = null;
      }

      setMicNode(null);
      setAudioNode(null);
      setAnalyserNode(null);
    }

    return () => {
      // Basic cleanup on unmount

      if (
        audioContextRef.current &&
        audioContextRef.current.state !== "closed"
      ) {
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
    // Given audio stream from the server socket, send it to playback processor

    if (audioNode && socketRef.current) {
      const handleAudioData = (data) => {
        const float32Array = new Float32Array(data);
        audioNode.port.postMessage({
          message: "audioData",
          audioData: float32Array,
        });
      };

      socketRef.current.on("audio", handleAudioData);

      return () => {
        if (socketRef.current) {
          socketRef.current.off("audio");
        }
      };
    }
  }, [audioNode]);

  useEffect(() => {
    // Given audio stream from the mic processor,
    // send it to the server socket

    if (micNode && socketRef.current) {
      micNode.port.onmessage = (event) => {
        if (socketRef.current && socketRef.current.connected) {
          socketRef.current.emit("audio_input", event.data.audioData);
        }
      };
    }
  }, [micNode]);

  useEffect(() => {
    // Show a simple activity widget for mic audio source

    if (analyserNode) {
      const canvas = canvasRef.current;
      const canvasContext = canvas.getContext("2d");

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

        canvasContext.fillStyle = "rgb(200, 200, 200)";
        canvasContext.fillRect(0, 0, canvas.width, canvas.height);

        const barWidth = (rms / 128) * canvas.width;

        canvasContext.fillStyle = "rgb(0, 0, 0)";
        canvasContext.fillRect(0, 0, barWidth, canvas.height);
      };

      renderFrame();
    }
  }, [analyserNode]);

  const startButtonHandler = () => {
    // Handle switch from open to not open and vv.
    setIsOpen((prevState) => !prevState);
  };

  const settingsHandler = () => {
    if (socketRef.current) {
      socketRef.current.emit("settings_update", settings);
    }
  };

  const handleThresholdChange = (event) => {
    // Simple setter for the slider
    setSettings({
      ...settings,
      threshold: parseFloat(event.target.value),
    });
  };

  const handleSystemPromptChange = (event) => {
    setSettings({
      ...settings,
      system_prompt: event.target.value,
    });
  };

  return (
    <div className="App">
      <div className="container">
        <div className="title">
          <h1>Teehetki</h1>
        </div>
        <div className="description">
          <p>
            Aloita, ja soketti lentää palvelimelle. Sen jälkeen voit puhua
            kunhan odotat kärsivällisesti vastausta.
          </p>
        </div>
        <div className="start-button">
          <button onClick={startButtonHandler}>
            {isOpen ? "Stop" : "Start"}
          </button>
        </div>
        <div
          className={`agent-status ${agentProcessing ? "processing" : "idle"}`}
        >
          <p>
            Status: <span>{agentProcessing ? "Processing" : "Idle"}</span>
          </p>
        </div>
        <div className="settings-section">
          <div className="threshold-slider">
            <label>VAD threshold:</label>
            <input
              type="range"
              min={thresholdMin}
              max={thresholdMax}
              step={thresholdStep}
              value={settings.threshold}
              onChange={handleThresholdChange}
            />
            <label>Value: {settings.threshold}</label>
          </div>
          <div className="system-prompt">
            <label>System Prompt:</label>
            <textarea
              value={settings.system_prompt}
              onChange={handleSystemPromptChange}
            />
          </div>
          <button onClick={settingsHandler} disabled={!isOpen}>
            Update settings
          </button>
        </div>
        <div className="canvas">
          <canvas ref={canvasRef}></canvas>
        </div>
        <div className="chat-history">
          <h2>Chat History</h2>
          {chatHistory.length > 0 ? (
            <ul>
              {chatHistory
                .slice()
                .reverse()
                .map((entry, index) => (
                  <li key={index} className={entry.role}>
                    <strong>{entry.role}:</strong> {entry.content}
                  </li>
                ))}
            </ul>
          ) : (
            <p>No chat history yet available.</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
