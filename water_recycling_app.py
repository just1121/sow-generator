import streamlit as st

# This must be the first Streamlit command
st.set_page_config(page_title="Water Recycling App", layout="wide")

# Now other imports
import os
import io
import re
import base64
import numpy as np

try:
    from docx import Document
    from docx.shared import Pt
    import google.generativeai as genai
    st.success("All core imports successful")
except Exception as e:
    st.error(f"Error importing: {e}")

# Rest of your minimal test app
st.title("Water Recycling Solution Generator")
st.write("Testing imports and basic functionality.")

# Add a simple interactive element
if st.button("Click me"):
    st.success("Button clicked!")

# Show some basic information
st.info("If you can see this, the app is working correctly.")