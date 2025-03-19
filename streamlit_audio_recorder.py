import os
import streamlit.components.v1 as components

_RELEASE = True

if not _RELEASE:
    _component_func = components.declare_component(
        "audio_recorder",
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "streamlit_audio_recorder", "frontend/build")
    print(f"Looking for build directory at: {build_dir}")
    _component_func = components.declare_component("audio_recorder", path=build_dir)

def st_audio_recorder(key=None):
    try:
        result = _component_func(key=key)
        print(f"Audio recorder result: {type(result)}, {result if result else 'None'}")
        return result
    except Exception as e:
        print(f"Error in audio recorder: {str(e)}")
        return None