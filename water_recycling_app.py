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
    st.success("All core imports successful")
except Exception as e:
    st.error(f"Error importing: {e}")

# Basic app UI
st.title("Water Recycling Solution Generator")
st.write("Testing form functionality")

# Form for input
with st.form("test_form"):
    name = st.text_input("Enter your name:")
    company = st.text_input("Enter your company:")
    submitted = st.form_submit_button("Submit")

# Process form submission outside the form
if submitted:
    st.write(f"Hello, {name} from {company}!")
    st.write("This confirms that basic form inputs are working.")
    
    # Create a simple Word document as a test
    try:
        doc = Document()
        doc.add_heading(f'Test Document for {name}', 0)
        doc.add_paragraph(f'This is a test document for {name} from {company}.')
        
        # Save to BytesIO
        doc_io = io.BytesIO()
        doc.save(doc_io)
        doc_io.seek(0)
        
        # Offer for download (outside the form)
        st.download_button(
            label="Download Test Document",
            data=doc_io,
            file_name="test_document.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        st.success("Document generation is working!")
    except Exception as e:
        st.error(f"Error generating document: {e}")
        st.exception(e)

# Show info message
st.info("If you can see this, all test functions are working.")