import streamlit as st
import pandas as pd
import datetime
from io import BytesIO

from utils.animations import animations
from streamlit_lottie import st_lottie

def backup_restore_page(conn):
    cursor = conn.cursor()

    st.markdown("## 💾 Backup & Restore")
    st.write("Download your database backup or export your ticket data to Excel. You can also restore your ticket data from an Excel file or a .db file.")
    
    st.subheader("Download Options")
    try:
        with open("ticket_management.db", "rb") as db_file:
            db_bytes = db_file.read()
        st.download_button("Download Database (.db)", db_bytes, file_name="ticket_management.db", mime="application/octet-stream")
    except Exception as e:
        st.error("Database file not found.")
    
    df_tickets = pd.read_sql("SELECT * FROM tickets", conn)
    if not df_tickets.empty:
        towrite = BytesIO()
        with pd.ExcelWriter(towrite, engine="xlsxwriter") as writer:
            df_tickets.to_excel(writer, index=False, sheet_name="Tickets")
        towrite.seek(0)
        st.download_button("Download Excel Backup", towrite.read(), file_name="tickets_backup.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("No ticket data available to export.")
    
    st.markdown("---")
    st.subheader("Restore from Excel")
    st.write("Upload an Excel file to restore your ticket data. **Warning:** This will overwrite your current ticket data.")
    uploaded_excel = st.file_uploader("Choose an Excel file", type=["xlsx"])
    if uploaded_excel is not None:
        try:
            df_restore = pd.read_excel(uploaded_excel)
            required_columns = {"date", "time", "batch_name", "ticket_number", "num_sub_tickets", "status", "pay", "comments", "ticket_day", "ticket_school"}
            if not required_columns.issubset(set(df_restore.columns)):
                st.error("Uploaded Excel file does not contain the required columns.")
            else:
                cursor.execute("DELETE FROM tickets")
                conn.commit()
                df_restore.to_sql("tickets", conn, if_exists="append", index=False)
                st.success("Database restored successfully from Excel file!")
        except Exception as e:
            st.error(f"Error restoring from Excel: {e}")
    
    st.markdown("---")
    st.subheader("Restore Database from .db File")
    st.write("Upload a .db file to restore your entire database. **Warning:** This will overwrite your current database.")
    uploaded_db = st.file_uploader("Choose a .db file", type=["db"])
    if uploaded_db is not None:
        try:
            with open("ticket_management.db", "wb") as f:
                f.write(uploaded_db.getbuffer())
            st.success("Database restored successfully from uploaded .db file!")
            conn.close()
            from utils.db import get_db_connection
            conn = get_db_connection()
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Error restoring database from .db file: {e}")
