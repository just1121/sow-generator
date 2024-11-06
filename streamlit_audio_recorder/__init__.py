import os
import streamlit.components.v1 as components
import streamlit as st
from google.cloud import speech_v1

_RELEASE = False

if not _RELEASE:
    _component_func = components.declare_component(
        "audio_recorder",
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("audio_recorder", path=build_dir)

def st_audio_recorder(key=None):
    """Create an audio recorder component"""
    audio_data = _component_func(key=key)
    if audio_data is not None:
        try:
            audio_bytes = bytes(audio_data['bytes'])
            
            # Create the Speech-to-Text client
            client = speech_v1.SpeechClient()
            
            # Configure the recognition
            audio = speech_v1.RecognitionAudio(content=audio_bytes)
            config = speech_v1.RecognitionConfig(
                encoding=speech_v1.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                sample_rate_hertz=48000,
                language_code="en-US",
                enable_automatic_punctuation=True,
            )

            # Perform the transcription
            response = client.recognize(config=config, audio=audio)
            
            # Get the transcription
            transcription = ""
            for result in response.results:
                transcription += result.alternatives[0].transcript
            
            # Return without displaying
            return audio_bytes, transcription
            
        except Exception as e:
            st.error(f"Error processing audio: {e}")
    return None, None