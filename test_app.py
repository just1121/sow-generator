import streamlit as st
from streamlit_audio_recorder import st_audio_recorder

# Page configuration
st.set_page_config(
    page_title="Audio Test",
    layout="centered"
)

# Main recorder - only get the transcription
_, transcription = st_audio_recorder()

# Only display transcription if available (don't show the duplicate)
if transcription:
    st.write(transcription)