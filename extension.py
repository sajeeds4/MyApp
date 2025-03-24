# extension.py
# At the top of your App.py file, add:
from extension import extension_page

# ...

def main():
    render_navbar()
    pages = {
        "Dashboard": dashboard_page,
        "Add Tickets": add_tickets_page,
        "View Tickets": view_tickets_page,
        "Manage Tickets": manage_tickets_page,
        "Income": income_page,
        "Batches": batch_view_page,
        "Settings": settings_page,
        "Extension": extension_page,  # Added extension page
    }
    active_page = st.session_state.active_page
    if active_page in pages:
        pages[active_page]()
    
    st.markdown(f"""
    <div style="text-align:center; padding: 15px; font-size: 0.8rem; border-top: 1px solid #ccc; margin-top: 30px;">
        <p>{st.session_state.company_name} Ticket System • {datetime.datetime.now().year}</p>
        <p>Powered by Streamlit • v1.0</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
