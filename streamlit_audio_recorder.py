import os
import streamlit.components.v1 as components
import streamlit as st

_RELEASE = True

if not _RELEASE:
    _component_func = components.declare_component(
        "audio_recorder",
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    print(f"Debug: Looking for build directory at: {build_dir}")
    print(f"Debug: Build directory exists: {os.path.exists(build_dir)}")
    print(f"Debug: Build directory contents: {os.listdir(build_dir) if os.path.exists(build_dir) else 'NOT FOUND'}")
    _component_func = components.declare_component("audio_recorder", path=build_dir)

def st_audio_recorder(key=None):
    try:
        result = _component_func(key=key)
        print(f"Debug: Component loaded with result: {result}")
        return result
    except Exception as e:
        print(f"Error in audio recorder: {str(e)}")
        return None

def get_audio_input(question, key):
    if key not in st.session_state:
        st.session_state[key] = ""
    
    # Create columns for layout with adjusted ratios
    col1, col2, col3 = st.columns([3, 0.5, 2])
    
    with col1:
        st.write(question)
    
    with col2:
        audio_bytes = st_audio_recorder(key=f"audio_{key}")
    
    with col3:
        text_value = st.text_area("", 
                                key=f"text_{key}", 
                                value=st.session_state[key],
                                height=100)
    
    if text_value != st.session_state[key]:
        st.session_state[key] = text_value
    
    return st.session_state[key]