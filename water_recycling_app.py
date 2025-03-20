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
st.write("Testing with Gemini 2.0 model")

# Configure API key
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Form for input
with st.form("test_form"):
    name = st.text_input("Enter your name:")
    company = st.text_input("Enter your company:")
    submitted = st.form_submit_button("Submit")

# Process form submission
if submitted:
    st.write(f"Hello, {name} from {company}!")
    
    # Try generating text with Gemini 2.0
    if name and company:
        try:
            prompt = f"Write a short greeting to {name} from {company} about water recycling and sustainability."
            
            # Use Gemini 2.0 Flash model
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt)
            
            st.subheader("Gemini 2.0 Response:")
            st.write(response.text)
            
            # Create document with the response
            doc = Document()
            doc.add_heading(f'Water Recycling Solution for {company}', 0)
            doc.add_paragraph(f'Generated for: {name}')
            doc.add_paragraph(response.text)
            
            # Save to BytesIO
            doc_io = io.BytesIO()
            doc.save(doc_io)
            doc_io.seek(0)
            
            # Offer for download
            st.download_button(
                label="Download Document",
                data=doc_io,
                file_name=f"{company}_water_recycling.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            
        except Exception as e:
            st.error(f"Error generating content: {e}")
            st.exception(e)

# Show info message
st.info("If you can see this, the Gemini 2.0 integration is working.")