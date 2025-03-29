import streamlit as st

def init_session_state():
    if "ticket_price" not in st.session_state:
        st.session_state.ticket_price = 5.5
    if "company_name" not in st.session_state:
        st.session_state.company_name = "My Business"
    if "batch_prefix" not in st.session_state:
        st.session_state.batch_prefix = "Batch-"
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False
    if "active_page" not in st.session_state:
        st.session_state.active_page = "Dashboard"  # default page
