import streamlit as st
import pandas as pd
import datetime
import sqlite3
import streamlit.components.v1 as components

from utils.animations import animations
from utils.status import db_status_from_ui, ui_status_from_db

from streamlit_lottie import st_lottie

def manage_tickets_page(conn):
    cursor = conn.cursor()

    col_anim, col_title = st.columns([1, 5])
    with col_anim:
        if animations["settings"]:
            st_lottie(animations["settings"], height=150, key="manage_anim")
    with col_title:
        st.markdown("## 🔄 Manage Tickets")
        st.write("Advanced ticket management operations")
    
    st.markdown("---")
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 Search & Edit",
        "⚡ Bulk Operations",
        "🗑️ Delete Tickets",
        "📦 By Batch",
        "💻 SQL Query"
    ])
    
    # Tab 1: Search & Edit
    with tab1:
        st.subheader("Individual Ticket Management")
        ticket_number = st.text_input("Enter Ticket Number to Manage")
        if ticket_number:
            ticket_data = pd.read_sql("SELECT * FROM tickets WHERE ticket_number = ?", conn, params=(ticket_number.strip(),))
            if not ticket_data.empty:
                current_status_ui = ui_status_from_db(ticket_data.iloc[0]['status'])
                with st.form("edit_ticket_form"):
                    new_status_ui = st.selectbox("Status", ["Intake", "Ready to Deliver", "Delivered"],
                                                 index=["Intake", "Ready to Deliver", "Delivered"].index(current_status_ui))
                    new_subtickets = st.number_input("Sub-Tickets", min_value=1, value=int(ticket_data.iloc[0]['num_sub_tickets']))
                    new_price = st.number_input("Ticket Price", min_value=0.0, value=float(ticket_data.iloc[0]['pay']), step=0.5)
                    if st.form_submit_button("Update Ticket"):
                        db_status = db_status_from_ui(new_status_ui)
                        cursor.execute("UPDATE tickets SET status = ?, num_sub_tickets = ?, pay = ? WHERE ticket_number = ?",
                                       (db_status, new_subtickets, new_price, ticket_number.strip()))
                        conn.commit()
                        st.success("Ticket updated successfully!")
                        if animations["success"]:
                            st_lottie(animations["success"], height=80)
            else:
                st.warning("Ticket not found in database")
    
    # Tab 2: Bulk Operations
    with tab2:
        st.subheader("Bulk Operations")
        bulk_tickets = st.text_area("Enter Ticket Numbers (one per line)", help="Enter one ticket number per line")
        bulk_action = st.selectbox("Action", ["Update Status", "Change Price", "Add Subtickets"])
        if bulk_tickets:
            ticket_list = [t.strip() for t in bulk_tickets.split('\n') if t.strip()]
            found_tickets = []
            missing_tickets = []
            for t in ticket_list:
                cursor.execute("SELECT 1 FROM tickets WHERE ticket_number = ?", (t,))
                if cursor.fetchone():
                    found_tickets.append(t)
                else:
                    missing_tickets.append(t)
            if missing_tickets:
                st.warning(
                    f"{len(missing_tickets)} tickets not found: "
                    + ", ".join(missing_tickets[:3])
                    + ("..." if len(missing_tickets) > 3 else "")
                )
            if found_tickets:
                st.success(f"{len(found_tickets)} valid tickets found")
                if bulk_action == "Update Status":
                    new_status_ui = st.selectbox("New Status", ["Intake", "Ready to Deliver", "Delivered"])
                    if st.button("Update Status for All Found Tickets"):
                        db_status = db_status_from_ui(new_status_ui)
                        for t in found_tickets:
                            cursor.execute("UPDATE tickets SET status = ? WHERE ticket_number = ?", (db_status, t))
                        conn.commit()
                        st.success(f"Updated {len(found_tickets)} tickets to {new_status_ui} status")
                elif bulk_action == "Change Price":
                    new_price = st.number_input("New Price", min_value=0.0, value=st.session_state.ticket_price)
                    if st.button("Update Price for All Found Tickets"):
                        for t in found_tickets:
                            cursor.execute("UPDATE tickets SET pay = ? WHERE ticket_number = ?", (new_price, t))
                        conn.commit()
                        st.success(f"Updated pricing for {len(found_tickets)} tickets")
                elif bulk_action == "Add Subtickets":
                    add_count = st.number_input("Additional Subtickets", min_value=1, value=1)
                    if st.button("Add Subtickets to All Found Tickets"):
                        for t in found_tickets:
                            cursor.execute("UPDATE tickets SET num_sub_tickets = num_sub_tickets + ? WHERE ticket_number = ?", (add_count, t))
                        conn.commit()
                        st.success(f"Added {add_count} subtickets to {len(found_tickets)} tickets")
    
    # Tab 3: Delete Tickets
    with tab3:
        st.subheader("Ticket Deletion")
        delete_option = st.radio("Deletion Method", ["Single Ticket", "By Batch", "By Date Range"])
        if delete_option == "Single Ticket":
            del_ticket = st.text_input("Enter Ticket Number to Delete")
            if del_ticket and st.button("Delete Ticket"):
                cursor.execute("DELETE FROM tickets WHERE ticket_number = ?", (del_ticket.strip(),))
                conn.commit()
                if cursor.rowcount > 0:
                    st.success("Ticket deleted successfully")
                else:
                    st.error("Ticket not found")
        elif delete_option == "By Batch":
            batch_name = st.text_input("Enter Batch Name to Delete")
            if batch_name and st.button("Delete Entire Batch"):
                cursor.execute("DELETE FROM tickets WHERE batch_name = ?", (batch_name.strip(),))
                conn.commit()
                st.success(f"Deleted {cursor.rowcount} tickets from batch {batch_name}")
        elif delete_option == "By Date Range":
            col_date1, col_date2 = st.columns(2)
            with col_date1:
                start_date = st.date_input("Start Date")
            with col_date2:
                end_date = st.date_input("End Date")
            if st.button("Delete Tickets in Date Range"):
                cursor.execute("DELETE FROM tickets WHERE date BETWEEN ? AND ?", (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
                conn.commit()
                st.success(f"Deleted {cursor.rowcount} tickets from {start_date} to {end_date}")
    
    # Tab 4: Manage Tickets By Batch
    with tab4:
        st.subheader("Manage Tickets By Batch Name")
        cursor.execute("SELECT DISTINCT batch_name FROM tickets")
        batch_rows = cursor.fetchall()
        batch_names = [row[0] for row in batch_rows if row[0]]
        if batch_names:
            selected_batch = st.selectbox("Select a Batch to Manage", batch_names)
            if selected_batch:
                df_batch = pd.read_sql("SELECT * FROM tickets WHERE batch_name = ?", conn, params=(selected_batch,))
                df_batch['status'] = df_batch['status'].apply(ui_status_from_db)
                st.dataframe(df_batch, use_container_width=True)
                new_status_ui = st.selectbox("New Status for All Tickets in This Batch", ["Intake", "Ready to Deliver", "Delivered"])
                if st.button("Update All Tickets in Batch"):
                    db_status = db_status_from_ui(new_status_ui)
                    cursor.execute("UPDATE tickets SET status = ? WHERE batch_name = ?", (db_status, selected_batch))
                    conn.commit()
                    st.success(f"All tickets in batch '{selected_batch}' updated to '{new_status_ui}'!")
                    df_batch = pd.read_sql("SELECT * FROM tickets WHERE batch_name = ?", conn, params=(selected_batch,))
                    df_batch['status'] = df_batch['status'].apply(ui_status_from_db)
                    st.dataframe(df_batch, use_container_width=True)
        else:
            st.info("No batches found in the database.")
    
    # Tab 5: Custom SQL Query Insert/Update
    with tab5:
        st.subheader("Custom SQL Query Insert/Update")
        st.write("Enter a valid SQL query (only INSERT or UPDATE queries are allowed) to update the tickets table. "
                 "This will modify ticket records and changes will reflect in the Intake, Ready to Deliver, and Delivered views.")
        sql_query = st.text_area("SQL Query", height=150,
                                 placeholder="e.g., INSERT INTO tickets (date, time, batch_name, ticket_number, num_sub_tickets, status, pay) VALUES ('2025-03-24', '12:34:56', 'Batch-100', 'TICKET123', 1, 'Intake', 5.5)")
        if st.button("Execute SQL Query"):
            if sql_query.strip():
                try:
                    cursor.execute(sql_query)
                    conn.commit()
                    st.success(f"Query executed successfully. Rows affected: {cursor.rowcount}")
                except Exception as e:
                    st.error(f"Error executing query: {e}")
            else:
                st.warning("Please enter a SQL query.")
    
    st.markdown("---")
