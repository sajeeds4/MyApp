import streamlit as st
import sqlite3
import pandas as pd
import datetime
import requests
import streamlit.components.v1 as components
from streamlit_lottie import st_lottie

# -----------------------------------------------------------
# Initialize Session State
# -----------------------------------------------------------
st.session_state.setdefault("ticket_price", 5.5)

# -----------------------------------------------------------
# Page Configuration & Simple CSS
# -----------------------------------------------------------
st.set_page_config(
    page_title="Ticket Management (No Charts + Day-wise Income)",
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
        color: white;
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
        <h1>Ticket Management (No Charts, Day-wise Income)</h1>
        <p>Manage your tickets at $5.5 each. Minimal approach, day-wise earnings only.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------------------------------------
# Optional Lottie Animation in Sidebar
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
# Database (SQLite) Connection
# -----------------------------------------------------------
def get_db_connection():
    conn = sqlite3.connect("ticket_management.db", check_same_thread=False)
    return conn

conn = get_db_connection()
cursor = conn.cursor()

# Create table if not exists
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
# Sidebar Navigation (No "Dashboard" with charts, but we keep "History" + new "Income" page)
# -----------------------------------------------------------
menu = st.sidebar.radio(
    "Navigation",
    ["Add Tickets", "Manage Tickets", "Income", "History", "Settings"],
    index=0
)

# -----------------------------------------------------------
# Page: Add Tickets
# -----------------------------------------------------------
def add_tickets_page():
    st.header("Add Intake Tickets")
    st.markdown("All new tickets are added with status='Intake'. Large tickets can represent multiple sub-tickets.")

    raw_batch = st.text_input("Batch Name (optional)")
    ticket_input_type = st.radio("Ticket Input Type", ["Single/Multiple (General)", "Large Ticket"], index=0)

    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.datetime.now().strftime("%H:%M:%S")

    if not raw_batch.strip():
        # auto-generate a batch
        cursor.execute("SELECT COUNT(DISTINCT batch_name) FROM tickets")
        batch_count = cursor.fetchone()[0] + 1
        batch_name = f"Batch-{batch_count}"
    else:
        batch_name = raw_batch.strip()

    if ticket_input_type == "Single/Multiple (General)":
        tickets_input = st.text_area("Enter Ticket(s) (space-separated)")
        if st.button("Add Ticket(s)"):
            if tickets_input.strip():
                tickets_list = tickets_input.strip().split()
                success_count = 0
                for t in tickets_list:
                    t = t.strip()
                    if t:
                        try:
                            cursor.execute(
                                """INSERT INTO tickets(date, time, batch_name, ticket_number, num_sub_tickets, status, pay)
                                   VALUES(?,?,?,?,?,?,?)""",
                                (
                                    current_date, current_time, batch_name, t, 1, "Intake",
                                    st.session_state.ticket_price
                                )
                            )
                            success_count += 1
                        except sqlite3.IntegrityError:
                            st.error(f"Ticket '{t}' already exists.")
                conn.commit()
                if success_count:
                    st.success(f"Added {success_count} ticket(s) to batch '{batch_name}'.")
                    st.balloons()
            else:
                st.error("Please enter ticket number(s).")
    else:
        # Large Ticket
        large_t = st.text_input("Large Ticket Number")
        sub_count = st.number_input("Number of Sub-Tickets", min_value=1, value=5, step=1)
        if st.button("Add Large Ticket"):
            if large_t.strip():
                try:
                    cursor.execute(
                        """INSERT INTO tickets(date, time, batch_name, ticket_number, num_sub_tickets, status, pay)
                           VALUES(?,?,?,?,?,?,?)""",
                        (
                            current_date, current_time, batch_name, large_t.strip(), sub_count, "Intake",
                            st.session_state.ticket_price
                        )
                    )
                    conn.commit()
                    st.success(f"Added large ticket '{large_t}' with {sub_count} sub-tickets to batch '{batch_name}'.")
                    st.balloons()
                except sqlite3.IntegrityError:
                    st.error("That large ticket number already exists.")
            else:
                st.error("Please enter a valid ticket number.")

# -----------------------------------------------------------
# Page: Manage Tickets
# -----------------------------------------------------------
def manage_tickets_page():
    st.header("Manage Tickets")
    # Show all tickets
    df_all = pd.read_sql("SELECT * FROM tickets ORDER BY date DESC", conn)
    st.dataframe(df_all)

    st.markdown("#### Update Ticket Status (Single)")
    ticket_edit = st.text_input("Ticket Number to Edit")
    new_status = st.selectbox("Set New Status", ["Intake", "Return"])
    if st.button("Update Ticket"):
        if ticket_edit.strip():
            cursor.execute("UPDATE tickets SET status=? WHERE ticket_number=?", (new_status, ticket_edit.strip()))
            conn.commit()
            st.success(f"Ticket '{ticket_edit.strip()}' updated to {new_status}")
        else:
            st.warning("Enter a valid ticket number.")

    st.markdown("#### Delete a Ticket (Single)")
    ticket_delete = st.text_input("Ticket Number to Delete")
    if st.button("Delete Ticket"):
        if ticket_delete.strip():
            cursor.execute("DELETE FROM tickets WHERE ticket_number=?", (ticket_delete.strip(),))
            conn.commit()
            st.success(f"Deleted ticket '{ticket_delete.strip()}'")
        else:
            st.warning("Enter a valid ticket number.")

    st.markdown("#### Bulk Update Status")
    tickets_bulk = st.text_area("Tickets to Update (space-separated)")
    bulk_status = st.selectbox("Status to Set in Bulk", ["Intake", "Return"])
    if st.button("Bulk Update"):
        if tickets_bulk.strip():
            tickets_list = tickets_bulk.strip().split()
            updated = 0
            for t in tickets_list:
                t = t.strip()
                cursor.execute("UPDATE tickets SET status=? WHERE ticket_number=?", (bulk_status, t))
                if cursor.rowcount > 0:
                    updated += 1
            conn.commit()
            st.success(f"Updated {updated} ticket(s) to '{bulk_status}'.")
        else:
            st.warning("Enter at least one ticket number for bulk update.")

# -----------------------------------------------------------
# Page: Income (Day-wise, from Returned Tickets)
# -----------------------------------------------------------
def income_page():
    st.header("Day-wise Returned Earnings")
    st.markdown("Shows how much you've earned *per day* from tickets with status = Return.")

    df = pd.read_sql("""
        SELECT date,
               SUM(num_sub_tickets * pay) AS day_earnings
        FROM tickets
        WHERE status='Return'
        GROUP BY date
        ORDER BY date DESC
    """, conn)

    if not df.empty:
        st.dataframe(df)
        total_earnings = df["day_earnings"].sum()
        st.write(f"**Total Returned Earnings:** ${total_earnings:.2f}")
    else:
        st.info("No returned tickets found.")

# -----------------------------------------------------------
# Page: History
# -----------------------------------------------------------
def history_page():
    st.header("History (Minimal, No Graphs)")
    df_hist = pd.read_sql(
        """SELECT batch_name,
                  COUNT(*) AS ticket_count,
                  SUM(num_sub_tickets) AS total_subtickets,
                  SUM(num_sub_tickets * pay) AS total_value
           FROM tickets
           GROUP BY batch_name
           ORDER BY batch_name""",
        conn
    )
    st.dataframe(df_hist)
    
    st.markdown("### Batch Details")
    for _, row in df_hist.iterrows():
        batch = row["batch_name"]
        if not batch:
            continue
        with st.expander(f"View Tickets for {batch}"):
            if st.button(f"Return all tickets for {batch}", key=f"btn_return_{batch}"):
                cursor.execute("UPDATE tickets SET status='Return' WHERE batch_name=?", (batch,))
                conn.commit()
                st.success(f"All tickets in batch '{batch}' updated to Return.")
            df_batch = pd.read_sql("SELECT * FROM tickets WHERE batch_name=?", conn, params=(batch,))
            st.dataframe(df_batch)

# -----------------------------------------------------------
# Page: Settings
# -----------------------------------------------------------
def settings_page():
    st.header("Settings")
    st.markdown("Adjust your ticket price (USD per sub-ticket).")

    new_price = st.number_input("Ticket Price (USD)", min_value=0.0,
                                value=st.session_state.ticket_price, step=0.5)
    st.session_state.ticket_price = new_price
    st.success("Price updated. All new tickets will use this price!")

# -----------------------------------------------------------
# Routing
# -----------------------------------------------------------
if menu == "Add Tickets" or menu == "Add Intake Tickets":
    add_tickets_page()
elif menu == "Manage Tickets":
    manage_tickets_page()
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
            &copy; 2025 Ticket Management App. Minimal version, day-wise earnings only.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
