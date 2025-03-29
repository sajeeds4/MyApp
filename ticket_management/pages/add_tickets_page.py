import streamlit as st
import datetime
import pandas as pd
import sqlite3

from utils.animations import animations
from streamlit_lottie import st_lottie

def add_tickets_page(conn):
    cursor = conn.cursor()

    col_anim, col_title = st.columns([1, 5])
    with col_anim:
        if animations["tickets"]:
            st_lottie(animations["tickets"], height=150, key="ticket_anim")
    with col_title:
        st.markdown("## ➕ Add New Tickets")
        st.write(f"Current ticket price: ${st.session_state.ticket_price:.2f} per sub-ticket")
    
    st.markdown("---")
    col1, col2 = st.columns([2, 1])
    with col1:
        batch_name = st.text_input("Batch Name (optional)", placeholder="Enter a meaningful batch name")
        ticket_input_type = st.radio("Ticket Input Type", ["Multiple/General", "Large Ticket"], horizontal=True)
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        if not batch_name.strip():
            cursor.execute("SELECT COUNT(DISTINCT batch_name) FROM tickets")
            batch_count = cursor.fetchone()[0] + 1
            batch_name = f"{st.session_state.batch_prefix}{batch_count}"
    with col2:
        st.markdown("""
        **Quick Instructions**
        1. Enter a batch name (optional).
        2. Choose an input type.
        3. Enter ticket number(s).
        4. Click the Add button.
        """)

    if ticket_input_type == "Multiple/General":
        tickets_text = st.text_area("Enter Ticket Number(s)", placeholder="Space or newline separated ticket numbers")
        if st.button("Add Tickets"):
            if tickets_text.strip():
                tickets_list = tickets_text.replace('\n', ' ').strip().split()
                success_count = 0
                failed_tickets = []
                for t in tickets_list:
                    t = t.strip()
                    if t:
                        try:
                            cursor.execute(
                                """INSERT INTO tickets (date, time, batch_name, ticket_number, num_sub_tickets, status, pay)
                                   VALUES(?,?,?,?,?,?,?)""",
                                (current_date, current_time, batch_name, t, 1, "Intake", st.session_state.ticket_price)
                            )
                            success_count += 1
                        except sqlite3.IntegrityError:
                            failed_tickets.append(t)
                conn.commit()
                if success_count:
                    st.success(f"Successfully added {success_count} ticket(s) to batch '{batch_name}'.")
                    if animations["success"]:
                        st_lottie(animations["success"], height=120)
                if failed_tickets:
                    st.warning(
                        f"Could not add {len(failed_tickets)} ticket(s) because they already exist: "
                        + ", ".join(failed_tickets[:5])
                        + ("..." if len(failed_tickets) > 5 else "")
                    )
            else:
                st.warning("Please enter ticket number(s).")
    else:
        col_large1, col_large2 = st.columns(2)
        with col_large1:
            large_ticket = st.text_input("Large Ticket Number", placeholder="Enter the main ticket number")
        with col_large2:
            sub_count = st.number_input("Number of Sub-Tickets", min_value=1, value=5, step=1)
        if st.button("Add Large Ticket"):
            if large_ticket.strip():
                try:
                    cursor.execute(
                        """INSERT INTO tickets (date, time, batch_name, ticket_number, num_sub_tickets, status, pay)
                           VALUES(?,?,?,?,?,?,?)""",
                        (current_date, current_time, batch_name, large_ticket.strip(), sub_count, "Intake", st.session_state.ticket_price)
                    )
                    conn.commit()
                    st.success(f"Added large ticket '{large_ticket}' with {sub_count} sub-tickets to batch '{batch_name}'.")
                    if animations["success"]:
                        st_lottie(animations["success"], height=120)
                except sqlite3.IntegrityError:
                    st.error(f"Ticket '{large_ticket.strip()}' already exists.")
            else:
                st.warning("Please enter a valid ticket number.")
    
    st.markdown("---")
    st.subheader("Recent Additions")
    df_recent = pd.read_sql("SELECT date, time, batch_name, ticket_number, num_sub_tickets, status FROM tickets ORDER BY id DESC LIMIT 5", conn)
    if not df_recent.empty:
        st.dataframe(df_recent, use_container_width=True)
    else:
        st.info("No recent tickets added.")
