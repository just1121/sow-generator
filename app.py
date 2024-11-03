import streamlit as st
from streamlit_audio_recorder import st_audio_recorder

def main():
    st.title("Audio Recorder Test")
    
    # Add debug info
    st.write("Debug: Component about to render")
    
    try:
        # Create audio recorder with debug info
        st.write("Attempting to create audio recorder...")
        audio_bytes = st_audio_recorder(key="audio_recorder")
        st.write(f"Audio recorder created, type: {type(audio_bytes)}")
        
        # Add more debug info
        st.write("Debug: Component rendered")
        st.write("Audio bytes:", audio_bytes)
        
        # Check if audio data exists
        if audio_bytes is not None:
            st.write("Debug: Audio received")
            # Display audio playback
            st.audio(audio_bytes, format='audio/webm')
            
            # Optional: Show the raw bytes for debugging
            st.write(f"Audio bytes length: {len(audio_bytes)}")
    except Exception as e:
        st.error(f"Error occurred: {str(e)}")
        st.write("Exception type:", type(e))

if __name__ == "__main__":
    main() 