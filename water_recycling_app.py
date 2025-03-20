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

# Try initializing the Gemini API
try:
    # Configure API key
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
    st.success("✅ Successfully connected to Gemini API")
except Exception as e:
    st.error(f"Error initializing Gemini API: {e}")
    st.exception(e)

# Basic app UI
st.title("Water Recycling Solution Generator")
st.write("Testing API connection and form functionality")

# Add a simple form
with st.form("test_form"):
    name = st.text_input("Enter your name:")
    company = st.text_input("Enter your company:")
    submit = st.form_submit_button("Submit")
    
    if submit:
        st.write(f"Hello, {name} from {company}!")
        
        # Try a simple AI generation
        try:
            prompt = f"Write a short greeting to {name} from {company} about water recycling."
            response = model.generate_content(prompt)
            st.write("Gemini says:")
            st.write(response.text)
        except Exception as e:
            st.error(f"Error generating content: {e}")

# Show info message
st.info("If you can see this, the form and API functions are working.")