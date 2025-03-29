import streamlit as st
import pandas as pd
import datetime

from utils.status import db_status_from_ui

def sql_query_converter_page(conn):
    cursor = conn.cursor()

    st.markdown("## SQL Query Converter")
    st.write("Paste your raw ticket data (each line should be in the format `TicketNumber - Description`) and choose a target status. "
             "This tool will extract the ticket numbers and update or insert them into the database as needed.")
    
    raw_text = st.text_area("Enter raw ticket data", placeholder="""125633 - Eastport-South Manor / Acer R752T
125632 - Eastport-South Manor / Acer R752T
125631 - Eastport-South Manor / Acer R752T""", height=200)
    
    target_status = st.selectbox("Select target status", ["Intake", "Ready to Deliver"])
    
    if st.button("Generate and Execute SQL Query"):
        lines = raw_text.strip().splitlines()
        ticket_numbers = []
        for line in lines:
            if " - " in line:
                ticket_number = line.split(" - ")[0].strip()
                ticket_numbers.append(ticket_number)
            else:
                parts = line.split()
                if parts:
                    ticket_numbers.append(parts[0].strip())

        db_status = "Intake" if target_status == "Intake" else "Return"
        
        if ticket_numbers:
            now_date = datetime.datetime.now().strftime("%Y-%m-%d")
            now_time = datetime.datetime.now().strftime("%H:%M:%S")

            # Insert or ignore tickets that do not exist
            insert_sql = """
                INSERT OR IGNORE INTO tickets (date, time, batch_name, ticket_number, num_sub_tickets, status, pay)
                VALUES (?, ?, ?, ?, 1, 'Intake', ?)
            """
            for tkt in ticket_numbers:
                try:
                    cursor.execute(insert_sql, (now_date, now_time, "Auto-Batch", tkt, st.session_state.ticket_price))
                except Exception as e:
                    st.error(f"Error inserting ticket {tkt}: {e}")
            conn.commit()

            # Update the status for all these tickets
            placeholders = ','.join('?' for _ in ticket_numbers)
            update_sql = f"UPDATE tickets SET status = ? WHERE ticket_number IN ({placeholders})"
            params = [db_status] + ticket_numbers
            try:
                cursor.execute(update_sql, params)
                conn.commit()
                st.success(f"Inserted/updated {cursor.rowcount} tickets to '{target_status}'.")
            except Exception as e:
                st.error(f"Error updating tickets to '{target_status}': {e}")
        else:
            st.warning("No ticket numbers found in the input.")
