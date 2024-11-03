import os
import streamlit.components.v1 as components

_RELEASE = False  # Set to True for production

if not _RELEASE:
    _component_func = components.declare_component(
        "audio_recorder",
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("audio_recorder", path=build_dir)

def st_audio_recorder():
    return _component_func() 