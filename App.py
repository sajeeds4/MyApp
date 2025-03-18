import streamlit as st
import sqlite3
import pandas as pd
import datetime
import plotly.express as px
from io import BytesIO
import requests
from streamlit_lottie import st_lottie

# -----------------------------------------------------------
# Page Configuration & Custom CSS for a Fully Graphical UI
# -----------------------------------------------------------
st.set_page_config(page_title="Ticket Management Dashboard", page_icon=":ticket:", layout="wide")
st.markdown(
    """
    <style>
    /* Global styling */
    body {
        background-color: #f5f5f5;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #333;
    }
    .block-container {
        padding: 2rem;
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0 0 15px rgba(0,0,0,0.1);
    }
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #ffffff;
    }
    /* Top Banner styling */
    .header-banner {
        background-image: url('https://via.placeholder.com/1500x200.png?text=Your+Business+Tagline');
        background-size: cover;
        background-position: center;
        border-radius: 10px;
        margin-bottom: 1rem;
        padding: 2rem;
        text-align: center;
        color: #ffffff;
    }
    .header-banner h1 {
        font-size: 3rem;
        font-weight: bold;
    }
    /* KPI card styling */
    .stMetric {
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0 0 8px rgba(0,0,0,0.1);
    }
    /* DataFrame styling */
    .dataframe th {
        background-color: #f0f0f0;
        color: #333;
    }
    /* Footer styling */
    .footer {
        text-align: center;
        font-size: 0.8rem;
        padding: 1rem;
        color: #777;
    }
    </style>
    """, unsafe_allow_html=True
)

# -----------------------------------------------------------
# Top Banner (Logo and Tagline)
# -----------------------------------------------------------
st.markdown(
    """
    <div class="header-banner">
        <h1>Ticket Management Dashboard</h1>
        <p>Your Business: Resolve tickets at $5.5 each for consistent earnings</p>
    </div>
    """, unsafe_allow_html=True
)

# -----------------------------------------------------------
# Sidebar Lottie Animation (Optional)
# -----------------------------------------------------------
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()
lottie_nav = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_mjlh3hcy.json")
if lottie_nav:
    st.sidebar.markdown("<h4 style='text-align: center;'>Navigation Animation</h4>", unsafe_allow_html=True)
    st_lottie(lottie_nav, height=150, key="nav")

# -----------------------------------------------------------
# Configurable Settings (stored in session state)
# -----------------------------------------------------------
if "ticket_price" not in st.session_state:
    st.session_state.ticket_price = 5.5

# -----------------------------------------------------------
# Database Connection & Table Setup
# -----------------------------------------------------------
@st.cache_resource
def get_db_connection():
    return sqlite3.connect("ticket_management.db", check_same_thread=False)
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    time TEXT,
    batch_name TEXT,
    ticket_number TEXT UNIQUE,
    num_sub_tickets INTEGER DEFAULT 1,
    status TEXT DEFAULT 'Open',
    type TEXT,
    pay REAL DEFAULT 5.5,
    comments TEXT DEFAULT '',
    ticket_day TEXT,
    ticket_school TEXT
)
''')
conn.commit()
cursor.execute("PRAGMA table_info(tickets)")
cols = [col[1] for col in cursor.fetchall()]
if "ticket_day" not in cols:
    cursor.execute("ALTER TABLE tickets ADD COLUMN ticket_day TEXT")
    conn.commit()
if "ticket_school" not in cols:
    cursor.execute("ALTER TABLE tickets ADD COLUMN ticket_school TEXT")
    conn.commit()

# -----------------------------------------------------------
# Function: Add Tickets Page (for Intake or Return)
# -----------------------------------------------------------
def add_tickets_page(ticket_category):
    st.subheader(f"Add {ticket_category} Tickets")
    st.markdown(
        """
        **Instructions:**
        - **General Ticket:** Paste or type multiple ticket numbers separated by whitespace.
        - **Large Ticket:** Enter one ticket number and specify the number of sub-tickets.
        """
    )
    # REQUIRED fields: Batch Name and Ticket School
    user_batch = st.text_input("Batch Name", placeholder="Enter batch name (required)")
    ticket_school = st.text_input("Ticket School", placeholder="Enter ticket school (required)")
    # Optional field: Ticket Day
    ticket_day = st.text_input("Ticket Day", placeholder="Enter ticket day (optional)")
    
    if user_batch.strip() == "" or ticket_school.strip() == "":
        st.error("Please enter both a Batch Name and a Ticket School.")
        return
    
    ticket_entry_type = st.radio("Select Ticket Entry Type", ["General Ticket", "Large Ticket"], index=0)
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    batch_name = user_batch.strip()
    
    if ticket_entry_type == "General Ticket":
        ticket_input = st.text_area("Enter Ticket Numbers", height=150, help="Separate ticket numbers with whitespace. Ex: 12345 12346 12347")
        if st.button("Add Tickets"):
            ticket_input = ticket_input.strip()
            if ticket_input:
                tickets = ticket_input.split()
                success_count = 0
                for tn in tickets:
                    tn = tn.strip()
                    if tn:
                        try:
                            cursor.execute(
                                """INSERT INTO tickets 
                                (date, time, batch_name, ticket_number, num_sub_tickets, type, pay, ticket_day, ticket_school)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                (current_date, current_time, batch_name, tn, 1, ticket_category, st.session_state.ticket_price, 
                                 ticket_day.strip() if ticket_day.strip() != "" else None, 
                                 ticket_school.strip())
                            )
                            success_count += 1
                        except sqlite3.IntegrityError:
                            st.error(f"Ticket '{tn}' already exists.")
                conn.commit()
                if success_count:
                    st.success(f"Successfully added {success_count} tickets for {ticket_category}.")
                    st.balloons()
            else:
                st.error("Please enter some ticket numbers.")
    elif ticket_entry_type == "Large Ticket":
        large_ticket = st.text_input("Enter Large Ticket Number", help="This ticket represents a group.")
        sub_ticket_count = st.number_input("Number of Sub-Tickets", min_value=1, value=1, step=1)
        if st.button("Add Large Ticket"):
            large_ticket = large_ticket.strip()
            if large_ticket:
                try:
                    cursor.execute(
                        """INSERT INTO tickets 
                        (date, time, batch_name, ticket_number, num_sub_tickets, type, pay, ticket_day, ticket_school)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (current_date, current_time, batch_name, large_ticket, sub_ticket_count, ticket_category, st.session_state.ticket_price,
                         ticket_day.strip() if ticket_day.strip() != "" else None,
                         ticket_school.strip())
                    )
                    conn.commit()
                    st.success(f"Successfully added large ticket '{large_ticket}' with {sub_ticket_count} sub-tickets for {ticket_category}.")
                    st.balloons()
                except sqlite3.IntegrityError:
                    st.error("Ticket number already exists.")
            else:
                st.error("Please enter a valid ticket number.")

# -----------------------------------------------------------
# Function: Manage Tickets Page (Placeholder)
# -----------------------------------------------------------
def manage_tickets_page():
    st.subheader("Manage Tickets")
    st.markdown("Use the filters below to locate and manage your tickets:")
    # Placeholder – replace with your full Manage Tickets implementation
    st.write("Manage Tickets functionality goes here.")

# -----------------------------------------------------------
# Function: Dashboard Page (Placeholder)
# -----------------------------------------------------------
def dashboard_page():
    st.subheader("Dashboard Analytics")
    st.markdown("Interactive charts and business insights will be displayed here.")
    # Placeholder – replace with your full Dashboard implementation
    st.write("Dashboard functionality goes here.")

# -----------------------------------------------------------
# Function: Settings Page
# -----------------------------------------------------------
def settings_page():
    st.subheader("Settings")
    new_price = st.number_input("Fixed Ticket Price", min_value=0.0, value=st.session_state.ticket_price, step=0.5)
    st.session_state.ticket_price = new_price
    st.success("Settings updated!")

# -----------------------------------------------------------
# Main App Layout Using Tabs
# -----------------------------------------------------------
main_tabs = st.tabs(["Add Tickets", "Manage Tickets", "Dashboard", "Settings"])

with main_tabs[0]:
    add_tabs = st.tabs(["Add Intake Tickets", "Add Return Tickets"])
    with add_tabs[0]:
        st.markdown("### Add Intake Tickets")
        add_tickets_page("Intake")
    with add_tabs[1]:
        st.markdown("### Add Return Tickets")
        add_tickets_page("Return")

with main_tabs[1]:
    manage_tickets_page()

with main_tabs[2]:
    dashboard_page()

with main_tabs[3]:
    settings_page()

# -----------------------------------------------------------
# Footer
# -----------------------------------------------------------
st.markdown(
    """
    <div class="footer">
        <p>&copy; 2025 Ticket Management App. All rights reserved.</p>
    </div>
    """, unsafe_allow_html=True
)
