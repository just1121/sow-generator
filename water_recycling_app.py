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

# Basic app UI
st.title("Water Recycling Solution Generator")
st.write("Testing AI functionality")

# Debug the Gemini version
try:
    st.write(f"Google Generative AI version: {genai.__version__}")
except:
    st.write("Could not determine Google Generative AI version")

# Try initializing Gemini with a more version-agnostic approach
try:
    # Configure API key
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    
    # Display available models (this should work regardless of API version)
    st.subheader("Available Models:")
    try:
        models = genai.list_models()
        for model in models:
            st.write(f"- {model.name}")
    except Exception as e:
        st.error(f"Error listing models: {e}")
    
    st.success("Successfully connected to Gemini API")
except Exception as e:
    st.error(f"Error initializing Gemini API: {e}")
    st.exception(e)

# Form for input
with st.form("test_form"):
    name = st.text_input("Enter your name:")
    company = st.text_input("Enter your company:")
    submitted = st.form_submit_button("Submit")

# Process form submission
if submitted:
    st.write(f"Hello, {name} from {company}!")
    
    # Try generating text if the form was submitted
    if name and company:
        try:
            st.subheader("Attempting AI Generation:")
            prompt = f"Write a short greeting to {name} from {company} about water recycling."
            
            # Display the prompt
            st.write("Prompt:", prompt)
            
            # Different methods to try based on API version
            try:
                # Method 1 (newer API)
                st.write("Trying newer API method...")
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(prompt)
                st.write("Response:", response.text)
            except Exception as e1:
                st.write(f"Method 1 failed: {str(e1)}")
                
                try:
                    # Method 2 (older API)
                    st.write("Trying older API method...")
                    response = genai.generate_text(
                        model='gemini-pro',
                        prompt=prompt
                    )
                    st.write("Response:", response.text)
                except Exception as e2:
                    st.write(f"Method 2 failed: {str(e2)}")
                    
                    # If all else fails
                    st.error("Could not generate text with Gemini API.")
                    st.exception(e1)
                    
        except Exception as e:
            st.error(f"Overall error in AI generation: {e}")
            st.exception(e)

# Show info message
st.info("All test code executed. Check for success/error messages above.")