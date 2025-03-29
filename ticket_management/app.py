import streamlit as st
import datetime

# Import from utils
from utils.session_state import init_session_state
from utils.style import load_css
from utils.animations import animations
from utils.db import setup_database, get_db_connection
from utils.status import ui_status_from_db, db_status_from_ui

# Import each page
from pages.dashboard_page import dashboard_page
from pages.add_tickets_page import add_tickets_page
from pages.view_tickets_page import view_tickets_page
from pages.manage_tickets_page import manage_tickets_page
from pages.bulk_ticket_comparison_page import bulk_ticket_comparison_page
from pages.sql_query_converter_page import sql_query_converter_page
from pages.income_page import income_page
from pages.batches_page import batch_view_page
from pages.ai_analysis_page import ai_analysis_page
from pages.backup_restore_page import backup_restore_page
from pages.settings_page import settings_page


def render_navbar():
    pages = {
        "Dashboard": "📊",
        "Add Tickets": "➕",
        "View Tickets": "👁️",
        "Manage Tickets": "🔄",
        "Bulk Ticket Comparison": "🔍",
        "SQL Query Converter": "📝",
        "Income": "💰",
        "Batches": "🗂️",
        "AI Analysis": "🤖",
        "Backup & Restore": "💾",
        "Settings": "⚙️"
    }
    st.markdown(f"""
    <div style="padding: 10px; background-color: #ffffff; border-radius: 8px; margin-bottom: 20px;">
        <h2 style="display:inline;">🎟️ {st.session_state.company_name} Ticket System</h2>
    </div>
    """, unsafe_allow_html=True)
    cols = st.columns(len(pages))
    for i, (page, icon) in enumerate(pages.items()):
        if cols[i].button(f"{icon} {page}"):
            st.session_state.active_page = page


def main():
    st.set_page_config(
        page_title="Ticket Management System",
        page_icon="🎟️",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Initialize session state if not set
    init_session_state()

    # Load custom CSS
    load_css()

    # Setup database / create table if not exists
    setup_database()
    conn = get_db_connection()

    # Render top nav
    render_navbar()

    # Page router
    active_page = st.session_state.active_page

    if active_page == "Dashboard":
        dashboard_page(conn)
    elif active_page == "Add Tickets":
        add_tickets_page(conn)
    elif active_page == "View Tickets":
        view_tickets_page(conn)
    elif active_page == "Manage Tickets":
        manage_tickets_page(conn)
    elif active_page == "Bulk Ticket Comparison":
        bulk_ticket_comparison_page(conn)
    elif active_page == "SQL Query Converter":
        sql_query_converter_page(conn)
    elif active_page == "Income":
        income_page(conn)
    elif active_page == "Batches":
        batch_view_page(conn)
    elif active_page == "AI Analysis":
        ai_analysis_page(conn)
    elif active_page == "Backup & Restore":
        backup_restore_page(conn)
    elif active_page == "Settings":
        settings_page()

    # Footer
    st.markdown(f"""
    <div style="text-align:center; padding: 15px; font-size: 0.8rem; border-top: 1px solid #ccc; margin-top: 30px;">
        <p>{st.session_state.company_name} Ticket System • {datetime.datetime.now().year}</p>
        <p>Powered by Streamlit • v1.0</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
