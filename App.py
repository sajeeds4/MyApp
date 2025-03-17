import streamlit as st
import sqlite3
import pandas as pd
import datetime

# Use a singleton so the database connection persists across reruns.
@st.experimental_singleton
def get_connection():
    conn = sqlite3.connect("ticket_management.db", check_same_thread=False)
    return conn

conn = get_connection()
cursor = conn.cursor()

# Create the Tickets table with a fixed price of 5.5 per ticket.
cursor.execute('''
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    time TEXT,
    batch_name TEXT,
    ticket_number TEXT UNIQUE,
    num_sub_tickets INTEGER DEFAULT 0,
    status TEXT DEFAULT 'Open',
    type TEXT,
    pay REAL DEFAULT 5.5
)
''')
conn.commit()

# Create the Users table.
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
''')
conn.commit()

# Insert a default user if one doesn't exist.
cursor.execute("SELECT * FROM users WHERE username = ?", ("admin",))
if cursor.fetchone() is None:
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", "password"))
    conn.commit()

# Initialize session state for login.
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

def login(username, password):
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    if user:
        st.session_state.logged_in = True
        st.session_state.username = username
        return True
    return False

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""

# Display login form if not logged in.
if not st.session_state.logged_in:
    st.sidebar.title("Login")
    login_username = st.sidebar.text_input("Username")
    login_password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if login(login_username, login_password):
            st.sidebar.success(f"Logged in as {login_username}")
        else:
            st.sidebar.error("Invalid username or password")
else:
    st.sidebar.write(f"Logged in as {st.session_state.username}")
    if st.sidebar.button("Logout"):
        logout()
        st.experimental_rerun()

# Only show the app if logged in.
if st.session_state.logged_in:
    menu = st.sidebar.radio("Menu", ["Add Tickets", "Manage Tickets", "Dashboard", "Users"])
    
    if menu == "Add Tickets":
        st.header("Add Tickets")
        # Select the ticket category.
        ticket_category = st.radio("Select Ticket Category", ["Intake", "Outgoing"])
        # Select the ticket entry type.
        ticket_entry_type = st.radio("Select Ticket Entry Type", ["General Ticket", "Large Ticket"])
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        # Generate a new batch name.
        cursor.execute("SELECT COUNT(DISTINCT batch_name) FROM tickets")
        batch_count = cursor.fetchone()[0] + 1
        batch_name = f"Batch-{batch_count}"
        
        if ticket_entry_type == "General Ticket":
            # Accept multiple ticket numbers separated by space.
            ticket_numbers_input = st.text_input("Ticket Numbers (separated by space):")
            if st.button("Add General Tickets"):
                ticket_numbers_input = ticket_numbers_input.strip()
                if ticket_numbers_input:
                    ticket_numbers = ticket_numbers_input.split()
                    success_count = 0
                    for tn in ticket_numbers:
                        tn = tn.strip()
                        if tn:
                            try:
                                cursor.execute('''
                                INSERT INTO tickets (date, time, batch_name, ticket_number, num_sub_tickets, type, pay)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                                ''', (current_date, current_time, batch_name, tn, 1, ticket_category, 5.5))
                                success_count += 1
                            except sqlite3.IntegrityError:
                                st.error(f"Ticket number '{tn}' already exists.")
                    conn.commit()
                    if success_count:
                        st.success(f"{success_count} general ticket(s) added as {ticket_category}!")
                else:
                    st.error("Please enter at least one ticket number.")
                    
        elif ticket_entry_type == "Large Ticket":
            large_ticket_number = st.text_input("Large Ticket Number:")
            num_tickets_inside = st.number_input("Number of Sub-Tickets", min_value=1, step=1, value=1)
            if st.button("Add Large Ticket"):
                large_ticket_number = large_ticket_number.strip()
                if large_ticket_number:
                    try:
                        cursor.execute('''
                        INSERT INTO tickets (date, time, batch_name, ticket_number, num_sub_tickets, type, pay)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (current_date, current_time, batch_name, large_ticket_number, num_tickets_inside, ticket_category, 5.5))
                        conn.commit()
                        st.success(f"Large ticket '{large_ticket_number}' with {num_tickets_inside} sub-tickets added as {ticket_category}!")
                    except sqlite3.IntegrityError:
                        st.error("Ticket number already exists.")
                else:
                    st.error("Please enter a valid large ticket number.")
    
    elif menu == "Manage Tickets":
        st.header("Manage Tickets")
        df = pd.read_sql("SELECT * FROM tickets", conn)
        st.dataframe(df)
        ticket_to_resolve = st.text_input("Enter Ticket Number to Resolve:")
        if st.button("Resolve Ticket"):
            ticket_number = ticket_to_resolve.strip()
            cursor.execute("UPDATE tickets SET status='Resolved' WHERE ticket_number=?", (ticket_number,))
            conn.commit()
            st.success(f"Ticket '{ticket_number}' resolved.")
    
    elif menu == "Dashboard":
        st.header("Dashboard")
        df = pd.read_sql("SELECT * FROM tickets", conn)
        total_tickets = df.shape[0]
        unresolved_tickets = df[df["status"] == "Open"].shape[0]
        resolved_tickets = df[df["status"] == "Resolved"].shape[0]
        total_pay = (df["pay"] * df["num_sub_tickets"]).sum()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Tickets", total_tickets)
        col2.metric("Resolved Tickets", resolved_tickets)
        col3.metric("Unresolved Tickets", unresolved_tickets)
        col4.metric("Total Pay", f"${total_pay:.2f}")
        st.dataframe(df)
    
    elif menu == "Users":
        st.header("User Management")
        sub_menu = st.radio("User Menu", ["Add User", "View Users"])
        if sub_menu == "Add User":
            new_username = st.text_input("New Username")
            new_password = st.text_input("New Password", type="password")
            if st.button("Add User"):
                if new_username and new_password:
                    try:
                        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (new_username, new_password))
                        conn.commit()
                        st.success(f"User '{new_username}' added!")
                    except sqlite3.IntegrityError:
                        st.error("Username already exists.")
                else:
                    st.error("Please enter a valid username and password.")
        elif sub_menu == "View Users":
            df_users = pd.read_sql("SELECT id, username FROM users", conn)
            st.dataframe(df_users)
else:
    st.write("Please log in to access the application.")
