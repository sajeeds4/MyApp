import streamlit as st
import sqlite3
import pandas as pd
import datetime
import requests
import streamlit.components.v1 as components
from streamlit_lottie import st_lottie

# -----------------------------------------------------------
# Session State
# -----------------------------------------------------------
st.session_state.setdefault("ticket_price", 5.5)

# -----------------------------------------------------------
# Basic Page Configuration & CSS
# -----------------------------------------------------------
st.set_page_config(
    page_title="Ticket Management (Minimal + Day-wise Income)",
    page_icon=":ticket:",
    layout="wide"
)

st.markdown(
    """
    <style>
    body {
        background-color: #f5f5f5;
        font-family: Arial, sans-serif;
    }
    .reportview-container .main .block-container {
        padding: 2rem;
        background-color: #fff;
        border-radius: 10px;
        box-shadow: 0 0 15px rgba(0,0,0,0.1);
        max-width: 1200px;
        margin: auto;
    }
    .sidebar .sidebar-content {
        background-color: #fff;
    }
    .header-banner {
        background-color: #555;
        border-radius: 10px;
        margin-bottom: 1rem;
        padding: 2rem;
        text-align: center;
        color: #fff;
    }
    .header-banner h1 {
        font-size: 2rem;
        margin: 0;
    }
    div.stButton > button {
        background-color: #4CAF50;
        color: #fff;
        font-size: 16px;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        cursor: pointer;
        transition: transform 0.2s, background-color 0.3s ease;
        box-shadow: 0 5px #999;
        margin: 0.5rem;
    }
    div.stButton > button:hover {
        background-color: #45a049;
    }
    div.stButton > button:active {
        background-color: #3e8e41;
        transform: translateY(4px);
        box-shadow: 0 2px #666;
    }
    input, textarea, select {
        font-size: 16px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------------------------------------
# Top Banner
# -----------------------------------------------------------
st.markdown(
    """
    <div class="header-banner">
        <h1>Ticket Management (Minimal + Day-wise Income)</h1>
        <p>Manage tickets at $5.5 each, day-wise earnings, separate pages for Intake/Return/Delivered, unmatched logic.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------------------------------------
# Optional: Lottie in Sidebar
# -----------------------------------------------------------
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_animation = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_mjlh3hcy.json")
if lottie_animation:
    st.sidebar.markdown("<h4 style='text-align:center;'>Welcome!</h4>", unsafe_allow_html=True)
    st_lottie(lottie_animation, height=150, key="lottie")

# -----------------------------------------------------------
# Database (SQLite)
# -----------------------------------------------------------
def get_db_connection():
    conn = sqlite3.connect("ticket_management.db", check_same_thread=False)
    return conn

conn = get_db_connection()
cursor = conn.cursor()

# Create tickets table if not exists
cursor.execute('''
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    time TEXT,
    batch_name TEXT,
    ticket_number TEXT UNIQUE,
    num_sub_tickets INTEGER DEFAULT 1,
    status TEXT DEFAULT 'Intake',
    pay REAL DEFAULT 5.5,
    comments TEXT DEFAULT '',
    ticket_day TEXT,
    ticket_school TEXT
)
''')
conn.commit()

# -----------------------------------------------------------
# Sidebar Navigation
# -----------------------------------------------------------
menu = st.sidebar.radio(
    "Navigation",
    [
        "Add Tickets",
        "Intake Tickets",
        "Returned Tickets",
        "Delivered Tickets",
        "Manage Tickets",
        "Income",
        "History",
        "Settings"
    ],
    index=0
)

# -----------------------------------------------------------
# Page: Add Tickets (All new => status='Intake')
# -----------------------------------------------------------
def add_tickets_page():
    st.header("Add Tickets (status='Intake')")
    st.markdown("Ticket Price per sub-ticket: $%.2f" % st.session_state.ticket_price)

    raw_batch = st.text_input("Batch Name (optional)")
    ticket_input_type = st.radio("Ticket Input Type", ["Multiple/General", "Large Ticket"], index=0)

    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.datetime.now().strftime("%H:%M:%S")

    if not raw_batch.strip():
        cursor.execute("SELECT COUNT(DISTINCT batch_name) FROM tickets")
        batch_count = cursor.fetchone()[0] + 1
        batch_name = f"Batch-{batch_count}"
    else:
        batch_name = raw_batch.strip()

    if ticket_input_type == "Multiple/General":
        tickets_text = st.text_area("Enter Ticket(s) (space-separated)")
        if st.button("Add Ticket(s)"):
            if tickets_text.strip():
                tickets_list = tickets_text.strip().split()
                success_count = 0
                for t in tickets_list:
                    t = t.strip()
                    if t:
                        try:
                            cursor.execute("""INSERT INTO tickets
                                (date, time, batch_name, ticket_number, num_sub_tickets, status, pay)
                                VALUES(?,?,?,?,?,?,?)""",
                                (
                                    current_date, current_time, batch_name, t, 1,
                                    "Intake", st.session_state.ticket_price
                                )
                            )
                            success_count += 1
                        except sqlite3.IntegrityError:
                            st.error(f"Ticket '{t}' already exists in DB.")
                conn.commit()
                if success_count:
                    st.success(f"Added {success_count} ticket(s) to batch '{batch_name}'.")
                    st.balloons()
            else:
                st.warning("Please enter ticket number(s).")
    else:
        # Large Ticket
        large_ticket = st.text_input("Large Ticket Number")
        sub_count = st.number_input("Number of Sub-Tickets", min_value=1, value=5, step=1)
        if st.button("Add Large Ticket"):
            if large_ticket.strip():
                try:
                    cursor.execute("""INSERT INTO tickets
                        (date, time, batch_name, ticket_number, num_sub_tickets, status, pay)
                        VALUES(?,?,?,?,?,?,?)""",
                        (
                            current_date, current_time, batch_name, large_ticket.strip(),
                            sub_count, "Intake", st.session_state.ticket_price
                        )
                    )
                    conn.commit()
                    st.success(f"Added large ticket '{large_ticket}' with {sub_count} sub-tickets to batch '{batch_name}'.")
                    st.balloons()
                except sqlite3.IntegrityError:
                    st.error(f"Ticket '{large_ticket.strip()}' already exists.")
            else:
                st.warning("Please enter a valid ticket number.")

# -----------------------------------------------------------
# Page: Intake Tickets (View only)
# -----------------------------------------------------------
def view_intake_tickets():
    st.header("Intake Tickets")
    df_intake = pd.read_sql("SELECT * FROM tickets WHERE LOWER(status)='intake' ORDER BY date DESC", conn)
    st.dataframe(df_intake)

# -----------------------------------------------------------
# Page: Returned Tickets (View only)
# -----------------------------------------------------------
def view_returned_tickets():
    st.header("Returned Tickets")
    df_return = pd.read_sql("SELECT * FROM tickets WHERE LOWER(status)='return' ORDER BY date DESC", conn)
    st.dataframe(df_return)

# -----------------------------------------------------------
# Page: Delivered Tickets (View only)
# -----------------------------------------------------------
def view_delivered_tickets():
    st.header("Delivered Tickets")
    df_delivered = pd.read_sql("SELECT * FROM tickets WHERE LOWER(status)='delivered' ORDER BY date DESC", conn)
    st.dataframe(df_delivered)

# -----------------------------------------------------------
# Page: Manage Tickets (Bulk update with unmatched logic)
# -----------------------------------------------------------
def manage_tickets():
    st.header("Manage Tickets (Bulk Update, Single Edit, Unmatched Logic)")
    df_all = pd.read_sql("SELECT * FROM tickets ORDER BY date DESC", conn)
    st.dataframe(df_all)

    # Single ticket edit
    st.markdown("### Single Ticket Edit")
    single_ticket_edit = st.text_input("Ticket Number to Edit")
    new_status_single = st.selectbox("New Status", ["Intake", "Return", "Delivered"])
    if st.button("Update Single Ticket"):
        if single_ticket_edit.strip():
            cursor.execute("UPDATE tickets SET status=? WHERE ticket_number=?",
                           (new_status_single, single_ticket_edit.strip()))
            if cursor.rowcount > 0:
                st.success(f"Ticket '{single_ticket_edit.strip()}' updated to {new_status_single}.")
            else:
                st.error(f"Ticket '{single_ticket_edit.strip()}' not found in DB.")
            conn.commit()
        else:
            st.warning("Please enter a valid ticket number to update.")

    # Single ticket deletion
    st.markdown("### Single Ticket Deletion")
    single_ticket_delete = st.text_input("Ticket Number to Delete")
    if st.button("Delete Ticket"):
        if single_ticket_delete.strip():
            cursor.execute("DELETE FROM tickets WHERE ticket_number=?", (single_ticket_delete.strip(),))
            if cursor.rowcount > 0:
                st.success(f"Deleted ticket '{single_ticket_delete.strip()}'.")
            else:
                st.error(f"Ticket '{single_ticket_delete.strip()}' not found in DB.")
            conn.commit()
        else:
            st.warning("Enter a valid ticket number to delete.")

    # Bulk update
    st.markdown("### Bulk Update Status")
    bulk_tickets = st.text_area("Ticket(s) to Update (space-separated)")
    bulk_options = ["Intake", "Return", "Delivered"]
    new_status_bulk = st.selectbox("Status for Found Tickets", bulk_options)
    unmatched_choices = ["Ignore (do nothing)", "Add as Intake", "Add as Return", "Add as Delivered"]
    unmatched_handling = st.selectbox("If ticket does NOT exist in DB, how to handle?", unmatched_choices)

    if st.button("Bulk Update"):
        if bulk_tickets.strip():
            tickets_list = bulk_tickets.strip().split()
            matched = 0
            unmatched = []
            for t in tickets_list:
                t = t.strip()
                cursor.execute("UPDATE tickets SET status=? WHERE ticket_number=?", (new_status_bulk, t))
                if cursor.rowcount > 0:
                    matched += 1
                else:
                    unmatched.append(t)
            conn.commit()

            st.success(f"Updated {matched} existing ticket(s) to '{new_status_bulk}'.")

            # Now handle unmatched
            if unmatched and unmatched_handling != "Ignore (do nothing)":
                if unmatched_handling == "Add as Intake":
                    new_status_for_unmatched = "Intake"
                elif unmatched_handling == "Add as Return":
                    new_status_for_unmatched = "Return"
                else:
                    new_status_for_unmatched = "Delivered"

                current_date = datetime.datetime.now().strftime("%Y-%m-%d")
                current_time = datetime.datetime.now().strftime("%H:%M:%S")
                unmatched_batch = "Unmatched-Batch"

                added_count = 0
                for ut in unmatched:
                    ut = ut.strip()
                    if ut:
                        try:
                            cursor.execute(
                                """INSERT INTO tickets(date, time, batch_name, ticket_number, num_sub_tickets, status, pay)
                                   VALUES(?,?,?,?,?,?,?)""",
                                (
                                    current_date,
                                    current_time,
                                    unmatched_batch,
                                    ut,
                                    1,
                                    new_status_for_unmatched,
                                    st.session_state.ticket_price
                                )
                            )
                            added_count += 1
                        except sqlite3.IntegrityError:
                            pass
                conn.commit()
                st.success(f"Added {added_count} new ticket(s) as '{new_status_for_unmatched}' into batch '{unmatched_batch}'.")
            else:
                if unmatched and unmatched_handling == "Ignore (do nothing)":
                    st.warning(f"Ignored nonexistent tickets: {', '.join(unmatched)}")
        else:
            st.warning("No tickets entered for bulk update.")

# -----------------------------------------------------------
# Page: Income (Day-wise from Delivered) with date range
# -----------------------------------------------------------
def income_page():
    st.header("Day-wise Delivered Earnings (Interactive Date Range)")

    start_dt = st.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
    end_dt = st.date_input("End Date", datetime.date.today())

    query = """
        SELECT date,
               SUM(num_sub_tickets * pay) AS day_earnings
        FROM tickets
        WHERE status='Delivered' AND date BETWEEN ? AND ?
        GROUP BY date
        ORDER BY date DESC
    """
    params = [start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d")]
    df = pd.read_sql(query, conn, params=params)

    if not df.empty:
        st.dataframe(df)
        total_earnings = df["day_earnings"].sum()
        st.write(f"**Delivered Earnings from {start_dt} to {end_dt}:** ${total_earnings:.2f}")
    else:
        st.info("No delivered tickets found in this date range.")

# -----------------------------------------------------------
# Page: History
# -----------------------------------------------------------
def history_page():
    st.header("History: Batches, Minimal Display")

    # 1) Show a summary by batch
    df_hist = pd.read_sql("""
        SELECT batch_name,
               COUNT(*) AS ticket_count,
               SUM(num_sub_tickets) AS total_subtickets,
               SUM(num_sub_tickets * pay) AS total_value
        FROM tickets
        GROUP BY batch_name
        ORDER BY batch_name
    """, conn)
    st.dataframe(df_hist)

    # 2) Show overall total tickets (sum of sub_tickets)
    cursor.execute("SELECT IFNULL(SUM(num_sub_tickets), 0) FROM tickets")
    row = cursor.fetchone()
    total_tickets = row[0] if row[0] else 0
    st.markdown(f"### Overall Total Tickets: {int(total_tickets)}")

    # 3) Provide batch details, with "Return all" or "Deliver all" buttons
    st.markdown("### Batch Details (Return All or Deliver All)")
    for _, row_item in df_hist.iterrows():
        batch = row_item["batch_name"]
        if not batch:
            continue
        with st.expander(f"View Tickets for {batch}"):
            colA, colB = st.columns([1,1])
            with colA:
                if st.button(f"Return all tickets for '{batch}'", key=f"return_{batch}"):
                    cursor.execute("UPDATE tickets SET status='Return' WHERE batch_name=?", (batch,))
                    conn.commit()
                    st.success(f"All tickets in batch '{batch}' marked as Return.")
            with colB:
                if st.button(f"Deliver all tickets for '{batch}'", key=f"deliver_{batch}"):
                    # set all to 'Delivered'
                    cursor.execute("UPDATE tickets SET status='Delivered' WHERE batch_name=?", (batch,))
                    conn.commit()
                    st.success(f"All tickets in batch '{batch}' marked as Delivered.")

            df_batch = pd.read_sql("SELECT * FROM tickets WHERE batch_name=?", conn, params=(batch,))
            st.dataframe(df_batch)

# -----------------------------------------------------------
# Page: Settings
# -----------------------------------------------------------
def settings_page():
    st.header("Settings")
    st.markdown("Adjust your ticket price (per sub-ticket).")

    new_price = st.number_input("Ticket Price (USD)", min_value=0.0, value=st.session_state.ticket_price, step=0.5)
    st.session_state.ticket_price = new_price
    st.success("Price updated! New tickets will use this price.")

# -----------------------------------------------------------
# Routing
# -----------------------------------------------------------
if menu == "Add Tickets":
    add_tickets_page()
elif menu == "Intake Tickets":
    view_intake_tickets()
elif menu == "Returned Tickets":
    view_returned_tickets()
elif menu == "Delivered Tickets":
    view_delivered_tickets()
elif menu == "Manage Tickets":
    manage_tickets()
elif menu == "Income":
    income_page()
elif menu == "History":
    history_page()
elif menu == "Settings":
    settings_page()

# -----------------------------------------------------------
# Footer
# -----------------------------------------------------------
st.markdown(
    """
    <hr>
    <div style="text-align:center;">
        <p style="font-size:0.8rem; color:#777;">
            &copy; 2025 Ticket Management App. Minimal version, day-wise delivered income, unmatched logic.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
