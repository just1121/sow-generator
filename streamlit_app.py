import streamlit as st

def main():
    st.title("Water Recycling App")
    st.write("This is your Streamlit app!")
    
    # Add your Streamlit app code here
    # For example:
    user_input = st.text_input("Enter some text:")
    if user_input:
        st.write(f"You entered: {user_input}")

if __name__ == "__main__":
    main()
    