import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

from utils.status import ui_status_from_db
from utils.animations import animations
from streamlit_lottie import st_lottie

def batch_view_page(conn):
    st.markdown("## 🗂️ Batch View")
    st.write("View batches as tiles by status. Click on 'Edit Status' to update its status or 'Copy Tickets' to copy all ticket numbers for that batch.")

    df_batches = pd.read_sql(
        """
        SELECT batch_name, 
               SUM(num_sub_tickets) as total_tickets, 
               GROUP_CONCAT(DISTINCT status) as statuses,
               GROUP_CONCAT(ticket_number) as ticket_numbers
        FROM tickets 
        GROUP BY batch_name
        """, conn
    )

    tab_intake, tab_ready, tab_delivered, tab_all = st.tabs([
        "Intake Batches", "Ready to Deliver Batches", "Delivered Batches", "All Batches"
    ])
    
    def display_batches(df, prefix):
        cols = st.columns(3)
        for idx, row in df.iterrows():
            status_str = row["statuses"]
            if "," in status_str:
                display_status = "Mixed"
            else:
                display_status = ui_status_from_db(status_str)
            with cols[idx % 3]:
                display_batch_tile(
                    batch_name=row["batch_name"],
                    total_tickets=row["total_tickets"],
                    status=display_status,
                    unique_key=f"{prefix}_{idx}",
                    ticket_numbers=row["ticket_numbers"]
                )
    
    with tab_intake:
        df_intake = df_batches[df_batches["statuses"] == "Intake"]
        if not df_intake.empty:
            display_batches(df_intake, prefix="intake")
        else:
            st.info("No Intake batches found.")
    
    with tab_ready:
        df_ready = df_batches[df_batches["statuses"] == "Return"]
        if not df_ready.empty:
            display_batches(df_ready, prefix="ready")
        else:
            st.info("No Ready to Deliver batches found.")
    
    with tab_delivered:
        df_delivered = df_batches[df_batches["statuses"] == "Delivered"]
        if not df_delivered.empty:
            display_batches(df_delivered, prefix="delivered")
        else:
            st.info("No Delivered batches found.")
    
    with tab_all:
        if not df_batches.empty:
            display_batches(df_batches, prefix="all")
        else:
            st.info("No batches found.")
    
    if "edit_batch" in st.session_state and st.session_state.get("edit_batch"):
        st.markdown("## Update Batch Status")
        batch_to_edit = st.session_state.edit_batch
        st.write(f"Updating status for batch: **{batch_to_edit}**")
        with st.form("update_batch_status_form"):
            new_status_ui = st.selectbox("Select new status", ["Intake", "Ready to Deliver", "Delivered"])
            submitted = st.form_submit_button("Update Batch Status")
            if submitted:
                from utils.status import db_status_from_ui
                db_status = db_status_from_ui(new_status_ui)
                cursor = conn.cursor()
                cursor.execute("UPDATE tickets SET status = ? WHERE batch_name = ?", (db_status, batch_to_edit))
                conn.commit()
                st.success(f"Batch '{batch_to_edit}' updated to '{new_status_ui}'!")
                st.session_state.edit_batch = None

def display_batch_tile(batch_name, total_tickets, status, unique_key, ticket_numbers):
    with st.container():
        st.markdown(f"""
        <div style="border: 1px solid #ccc; border-radius: 8px; padding: 15px; margin: 5px; text-align: center;">
          <h4>{batch_name}</h4>
          <p>Total Tickets: {total_tickets}</p>
          <p>Status: {status}</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Edit Status", key=f"edit_btn_{unique_key}"):
            st.session_state.edit_batch = batch_name

        if st.button("Copy Tickets", key=f"copy_btn_{unique_key}"):
            random_suffix = f"copy_{unique_key}"
            html_code = f"""
            <input id="copyInput_{random_suffix}" 
                   type="text" 
                   value="{ticket_numbers}" 
                   style="opacity: 0; position: absolute; left: -9999px;">
            <button onclick="copyText_{random_suffix}()">Click to Copy Tickets</button>
            <script>
            function copyText_{random_suffix}() {{
                var copyText = document.getElementById("copyInput_{random_suffix}");
                copyText.select();
                document.execCommand("copy");
                alert("Copied tickets: " + copyText.value);
            }}
            </script>
            """
            components.html(html_code, height=50)
