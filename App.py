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
cursor = conn.cursor()
cursor.execute("SELECT COUNT(DISTINCT batch_name) FROM tickets")
batch_count = cursor.fetchone()[0] + 1
batch_name = f"Batch-{batch_name}"

# Menu
menu = st.sidebar.selectbox("Menu", ["Add Tickets", "Manage Tickets", "Dashboard"])

if menu == "Add Tickets":
    st.header("Add Large Tickets and Sub-Tickets")

    large_ticket_number = st.text_input("Large Ticket Number:")
    num_tickets_inside = st.number_input("Number of Tickets Inside", min_value=1, step=1, value=1)
    ticket_type = st.radio("Ticket Type", ["Intake", "Outgoing"])
    ticket_pay = st.number_input("Pay per Sub-Ticket:", min_value=0.0, step=0.5)

    if st.button("Add Large Ticket"):
        if large_ticket := large_ticket.strip():
            cursor.execute('''INSERT OR IGNORE INTO tickets
                              (date, time, batch_name, ticket_number, num_sub_tickets, type, pay)
                              VALUES (?, ?, ?, ?, ?, ?, ?)''',
                           (current_date, datetime.datetime.now().strftime("%H:%M:%S"),
                            batch_name, large_ticket, num_sub_tickets,
                            ticket_type, ticket_pay))
            conn.commit()
            st.success(f"Large ticket '{large_ticket}' with {num_sub_tickets} sub-tickets added!")
        else:
            st.error("Please enter a valid ticket number.")

elif menu == "Manage Tickets":
    st.header("Manage Tickets")
    df = pd.read_sql("SELECT * FROM tickets", conn)
    st.dataframe(df)

elif menu == "Dashboard":
    st.header("Dashboard")
    df = pd.read_sql("SELECT * FROM tickets", conn)

    total_tickets = df.shape[0]
    unresolved_tickets = df[df["status"] == "Open"].shape[0]
    resolved_tickets = df[df["status"] == "Resolved"].shape[0]
    total_pay = df["pay"].sum()

    st.metric("Total Tickets", total_tickets)
    st.metric("Resolved Tickets", resolved_tickets)
    st.metric("Unresolved Tickets", unresolved_tickets)
    st.metric("Total Pay", f"${df['pay'].sum():.2f}")

    st.dataframe(df)

elif menu == "Manage Tickets":
    st.header("Manage Tickets")

    df = pd.read_sql("SELECT * FROM tickets", conn)
    st.dataframe(df)

    ticket_to_resolve = st.text_input("Enter Ticket Number to Resolve:")

    if st.button("Resolve Ticket"):
        cursor.execute("UPDATE tickets SET status='Resolved' WHERE ticket_number=?", (ticket_number,))
        conn.commit()
        st.success(f"Ticket '{ticket_number}' resolved.")

# Close Database Connection
conn.close()
