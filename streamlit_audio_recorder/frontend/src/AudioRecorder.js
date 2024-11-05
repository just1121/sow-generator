import React, { useEffect, useState } from 'react';
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib";

const AudioRecorder = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);

  useEffect(() => {
    console.log("Component mounted");
    Streamlit.setFrameHeight(40);
    Streamlit.setComponentReady();
  }, []);

  const startRecording = async () => {
    console.log("Starting recording...");
    try {
      // Check if mediaDevices is available
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("Media devices API not supported in this browser");
      }

      const permission = await navigator.permissions.query({ name: 'microphone' });
      console.log("Microphone permission status:", permission.state);

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
        video: false  // Explicitly disable video
      });
      console.log("Got media stream:", stream);
      
      const recorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      console.log("Created MediaRecorder:", recorder);

      const chunks = [];
      recorder.ondataavailable = (event) => {
        console.log("Data available from recorder, size:", event.data.size);
        chunks.push(event.data);
      };

      recorder.onstop = () => {
        console.log("Recorder stopped, processing chunks:", chunks.length);
        const audioBlob = new Blob(chunks, { type: "audio/webm" });
        console.log("Created audio blob, size:", audioBlob.size);
        handleAudioRecording(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      recorder.onerror = (e) => {
        console.error("Recorder error:", e);
      };

      recorder.start(1000);
      console.log("Recorder started");
      setMediaRecorder(recorder);
      setAudioChunks(chunks);
      setIsRecording(true);
    } catch (err) {
      console.error("Error accessing microphone:", err);
      alert("Error accessing microphone: " + err.message);
    }
  };

  const handleAudioRecording = (audioBlob) => {
    console.log("Processing audio blob:", audioBlob.size);
    const reader = new FileReader();
    reader.onloadend = () => {
      const audioArray = new Uint8Array(reader.result);
      console.log("Sending audio data to Streamlit, size:", audioArray.length);
      Streamlit.setComponentValue({
        bytes: Array.from(audioArray),
        type: "audio/webm"
      });
    };
    reader.onerror = (error) => {
      console.error("FileReader error:", error);
    };
    reader.readAsArrayBuffer(audioBlob);
  };

  const stopRecording = () => {
    console.log("Stopping recording...");
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      console.log("MediaRecorder state:", mediaRecorder.state);
      mediaRecorder.stop();
      console.log("MediaRecorder stopped");
      setIsRecording(false);
    }
  };

  const handleClick = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const containerStyle = {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    width: "100%",
    height: "40px",
    padding: "0",
    margin: "0"
  };

  const buttonStyle = {
    backgroundColor: isRecording ? "#ff4444" : "#4CAF50",
    color: "white",
    padding: "8px 16px",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "14px",
    fontWeight: "bold",
    width: "80px",
    height: "32px"
  };

  return (
    <div style={containerStyle}>
      <button 
        onClick={handleClick}
        style={buttonStyle}
      >
        {isRecording ? "Stop" : "Speak"}
      </button>
    </div>
  );
};

export default withStreamlitConnection(AudioRecorder);