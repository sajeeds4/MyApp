import streamlit as st
import pandas as pd

from utils.status import ui_status_from_db

def view_tickets_page(conn):
    st.markdown("## 👁️ View Tickets by Status")
    tab1, tab2, tab3 = st.tabs(["📥 Intake", "🔄 Ready to Deliver", "🚚 Delivered"])
    
    with tab1:
        st.subheader("Intake Tickets")
        df_intake = pd.read_sql("SELECT * FROM tickets WHERE status='Intake' ORDER BY date DESC, time DESC", conn)
        if not df_intake.empty:
            df_intake['status'] = df_intake['status'].apply(ui_status_from_db)
            st.dataframe(df_intake, use_container_width=True)
            total_intake = df_intake['num_sub_tickets'].sum()
            total_value = total_intake * st.session_state.ticket_price
            col1, col2 = st.columns(2)
            col1.metric("Total Sub-Tickets", f"{int(total_intake)}")
            col2.metric("Total Value", f"${total_value:,.2f}")
        else:
            st.info("No intake tickets found")
    
    with tab2:
        st.subheader("Ready to Deliver Tickets")
        df_ready = pd.read_sql("SELECT * FROM tickets WHERE status='Return' ORDER BY date DESC, time DESC", conn)
        if not df_ready.empty:
            df_ready['status'] = df_ready['status'].apply(ui_status_from_db)
            st.dataframe(df_ready, use_container_width=True)
            total_ready = df_ready['num_sub_tickets'].sum()
            potential_value = total_ready * st.session_state.ticket_price
            col1, col2 = st.columns(2)
            col1.metric("Total Ready for Delivery", f"{int(total_ready)}")
            col2.metric("Potential Value", f"${potential_value:,.2f}")
        else:
            st.info("No 'Ready to Deliver' tickets found")
    
    with tab3:
        st.subheader("Delivered Tickets")
        df_delivered = pd.read_sql("SELECT * FROM tickets WHERE status='Delivered' ORDER BY date DESC, time DESC", conn)
        if not df_delivered.empty:
            df_delivered['status'] = df_delivered['status'].apply(ui_status_from_db)
            st.dataframe(df_delivered, use_container_width=True)
            total_delivered = df_delivered['num_sub_tickets'].sum()
            earned_value = total_delivered * st.session_state.ticket_price
            col1, col2 = st.columns(2)
            col1.metric("Total Delivered", f"{int(total_delivered)}")
            col2.metric("Earned Value", f"${earned_value:,.2f}")
        else:
            st.info("No delivered tickets found")
