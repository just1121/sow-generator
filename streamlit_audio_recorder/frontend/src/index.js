import React from "react";
import ReactDOM from "react-dom";
import AudioRecorder from "./AudioRecorder";

console.log("index.js starting");

const root = document.getElementById("root");
console.log("Root element:", root);

// Always render with Streamlit wrapper
ReactDOM.render(
  <AudioRecorder />,
  root
);