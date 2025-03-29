import streamlit as st

def load_css():
    if st.session_state.dark_mode:
        primary_color = "#1E88E5"
        bg_color = "#121212"
        text_color = "#E0E0E0"
    else:
        primary_color = "#4CAF50"
        bg_color = "#f8f9fa"
        text_color = "#333333"
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {bg_color};
            color: {text_color};
        }}
        /* Hide Streamlit Branding */
        #MainMenu, footer, header {{
            visibility: hidden;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
