import streamlit as st
import sqlite3
import pandas as pd
import datetime

# Database Connection
conn = sqlite3.connect("ticket_management.db", check_same_thread=False)
cursor = conn.cursor()

# Create Tables with Large Ticket Support
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
    pay REAL DEFAULT 0.0
)
''')
conn.commit()

# Get Current Date and Time
current_date = datetime.datetime.now().strftime("%Y-%m-%d")
current_time = datetime.datetime.now().strftime("%H:%M:%S")

# Get Batch Number
cursor.execute("SELECT COUNT(DISTINCT batch_name) FROM tickets")
batch_count = cursor.fetchone()[0] + 1
batch_name = f"Batch-{batch_count}"

# Menu
menu = st.sidebar.selectbox("Menu", ["Add Tickets", "Manage Tickets", "Dashboard"])

if menu == "Add Tickets":
    st.header("Add Large Tickets and Sub-Tickets")

    large_ticket_number = st.text_input("Large Ticket Number:")
    num_tickets_inside = st.number_input("Number of Tickets Inside", min_value=1, step=1, value=1)
    ticket_type = st.radio("Ticket Type", ["Intake", "Outgoing"])
    ticket_pay = st.number_input("Pay per Sub-Ticket:", min_value=0.0, step=0.5)

    if st.button("Add Large Ticket"):
        large_ticket = large_ticket_number.strip()
        if large_ticket:
            cursor.execute('''INSERT OR IGNORE INTO tickets
                              (date, time, batch_name, ticket_number, num_sub_tickets, type, pay)
                              VALUES (?, ?, ?, ?, ?, ?, ?)''',
                           (current_date, current_time,
                            batch_name, large_ticket, num_tickets_inside,
                            ticket_type, ticket_pay))
            conn.commit()
            st.success(f"Large ticket '{large_ticket}' with {num_tickets_inside} sub-tickets added!")
        else:
            st.error("Please enter a valid ticket number.")

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

# Close Database Connection
conn.close()
