import streamlit as st
import sqlite3
import pandas as pd
import datetime

# Cache the database connection so it persists across reruns and sessions.
@st.cache_resource
def get_db_connection():
    conn = sqlite3.connect("ticket_management.db", check_same_thread=False)
    return conn

conn = get_db_connection()
cursor = conn.cursor()

# Create the Tickets table (if it doesn't already exist)
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

# Sidebar menu (no login/user options)
menu = st.sidebar.radio("Menu", ["Add Tickets", "Manage Tickets", "Dashboard"])

if menu == "Add Tickets":
    st.header("Add Tickets")
    # Select Ticket Category (Intake or Outgoing)
    ticket_category = st.radio("Select Ticket Category", ["Intake", "Outgoing"])
    # Select Ticket Entry Type (General Ticket or Large Ticket)
    ticket_entry_type = st.radio("Select Ticket Entry Type", ["General Ticket", "Large Ticket"])
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    
    # Generate a new batch name based on the number of distinct batches.
    cursor.execute("SELECT COUNT(DISTINCT batch_name) FROM tickets")
    batch_count = cursor.fetchone()[0] + 1
    batch_name = f"Batch-{batch_count}"
    
    if ticket_entry_type == "General Ticket":
        # Accept multiple ticket numbers separated by space.
        ticket_numbers_input = st.text_input("Enter Ticket Numbers (separated by space):")
        if st.button("Add General Tickets"):
            ticket_numbers_input = ticket_numbers_input.strip()
            if ticket_numbers_input:
                ticket_numbers = ticket_numbers_input.split()
                success_count = 0
                for tn in ticket_numbers:
                    tn = tn.strip()
                    if tn:
                        try:
                            cursor.execute("""
                            INSERT INTO tickets (date, time, batch_name, ticket_number, num_sub_tickets, type, pay)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (current_date, current_time, batch_name, tn, 1, ticket_category, 5.5))
                            success_count += 1
                        except sqlite3.IntegrityError:
                            st.error(f"Ticket number '{tn}' already exists.")
                conn.commit()
                if success_count:
                    st.success(f"Added {success_count} general ticket(s) as {ticket_category}.")
            else:
                st.error("Please enter at least one ticket number.")
                    
    elif ticket_entry_type == "Large Ticket":
        # Provide a text input for the large ticket number and a number input for sub-tickets.
        large_ticket_number = st.text_input("Enter Large Ticket Number:")
        num_sub_tickets = st.number_input("Number of Sub-Tickets", min_value=1, step=1, value=1)
        if st.button("Add Large Ticket"):
            large_ticket_number = large_ticket_number.strip()
            if large_ticket_number:
                try:
                    cursor.execute("""
                    INSERT INTO tickets (date, time, batch_name, ticket_number, num_sub_tickets, type, pay)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (current_date, current_time, batch_name, large_ticket_number, num_sub_tickets, ticket_category, 5.5))
                    conn.commit()
                    st.success(f"Added large ticket '{large_ticket_number}' with {num_sub_tickets} sub-tickets as {ticket_category}.")
                except sqlite3.IntegrityError:
                    st.error("Ticket number already exists.")
            else:
                st.error("Please enter a valid ticket number.")

elif menu == "Manage Tickets":
    st.header("Manage Tickets")
    # Display all tickets from the database.
    df = pd.read_sql("SELECT * FROM tickets", conn)
    st.dataframe(df)
    
    # Option to mark a ticket as resolved.
    ticket_to_resolve = st.text_input("Enter Ticket Number to Resolve:")
    if st.button("Resolve Ticket"):
        ticket_to_resolve = ticket_to_resolve.strip()
        cursor.execute("UPDATE tickets SET status='Resolved' WHERE ticket_number=?", (ticket_to_resolve,))
        conn.commit()
        st.success(f"Ticket '{ticket_to_resolve}' resolved.")

elif menu == "Dashboard":
    st.header("Dashboard")
    # Retrieve all tickets for dashboard metrics.
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
