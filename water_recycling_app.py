import streamlit as st

# Set page config
st.set_page_config(page_title="Water Recycling App", layout="wide")

# Basic content
st.title("Water Recycling Solution Generator")
st.write("This is a minimal test version to confirm basic functionality.")

# Add a simple interactive element
if st.button("Click me"):
    st.success("Button clicked!")

# Show some basic information
st.info("If you can see this, the app is working correctly.")