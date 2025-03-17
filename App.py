import streamlit as st
import sqlite3
import pandas as pd
import datetime

# Database Connection
conn = sqlite3.connect("ticket_management.db", check_same_thread=False)
cursor = conn.cursor()

# Create Tables
cursor.execute('''CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    time TEXT,
                    batch_name TEXT,
                    ticket_number TEXT,
                    status TEXT,
                    type TEXT,  -- 'intake' or 'outgoing'
                    pay_per_ticket REAL
                )''')
conn.commit()

# Get Current Date, Time, and Weekday
current_date = datetime.datetime.now().strftime("%Y-%m-%d")
current_time = datetime.datetime.now().strftime("%H:%M:%S")
weekday = datetime.datetime.now().strftime("%A")  # Monday, Tuesday, etc.

# Get Batch Number
cursor.execute("SELECT COUNT(*) FROM tickets WHERE date = ?", (current_date,))
batch_number = cursor.fetchone()[0] + 1
batch_name = f"{weekday} Batch {batch_number}"

# Sidebar Navigation
st.sidebar.title("📋 Ticket Management")
menu = st.sidebar.radio("Navigation", ["➕ Add Tickets", "📊 Dashboard & Analytics", "🗂 Manage Tickets"])

# **➕ Add New Tickets**
if menu == "➕ Add Tickets":
    st.title("➕ Add Intake & Outgoing Tickets")
    ticket_numbers = st.text_area("Enter Ticket Numbers (comma-separated):", placeholder="E.g., 1234, 5678, 91011")
    ticket_type = st.radio("Select Ticket Type:", ["Intake", "Outgoing"])
    pay_per_ticket = st.number_input("Enter Pay Per Ticket ($):", min_value=0.0, value=5.0, step=0.5)

    if st.button("Save Tickets"):
        ticket_list = [t.strip() for t in ticket_numbers.split(",") if t.strip()]
        if ticket_list:
            for ticket in ticket_list:
                cursor.execute("INSERT INTO tickets (date, time, batch_name, ticket_number, status, type, pay_per_ticket) VALUES (?, ?, ?, ?, ?, ?, ?)",
                               (current_date, current_time, batch_name, ticket, "Unresolved", ticket_type.lower(), pay_per_ticket))
            conn.commit()
            st.success(f"✅ {len(ticket_list)} {ticket_type.lower()} tickets added under '{batch_name}'!")
        else:
            st.error("⚠️ Please enter at least one ticket number.")

# **📊 Dashboard & Analytics**
elif menu == "📊 Dashboard & Analytics":
    st.title("📊 Ticket Analytics Dashboard")
    df = pd.read_sql("SELECT * FROM tickets", conn)

    if not df.empty:
        df["Total Pay"] = df["pay_per_ticket"]

        # Metrics
        total_tickets = len(df)
        unresolved_tickets = len(df[df["status"] == "Unresolved"])
        resolved_tickets = len(df[df["status"] == "Resolved"])
        total_earnings = df["Total Pay"].sum()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🎟 Total Tickets", total_tickets)
        col2.metric("⏳ Unresolved Tickets", unresolved_tickets)
        col3.metric("✅ Resolved Tickets", resolved_tickets)
        col4.metric("💰 Total Earnings", f"${total_earnings:.2f}")

        # Tickets by Type
        st.write("### 📦 Tickets by Type")
        ticket_summary = df.groupby("type").agg({"ticket_number": "count"})
        st.bar_chart(ticket_summary)

        # Batch Breakdown
        st.write("### 🏅 Batch Breakdown")
        batch_summary = df.groupby("batch_name").agg({"ticket_number": "count"})
        st.bar_chart(batch_summary)

    else:
        st.info("ℹ️ No ticket data available. Add tickets to see analytics.")

# **🗂 Manage Tickets**
elif menu == "🗂 Manage Tickets":
    st.title("🗂 Manage & Resolve Tickets")
    df = pd.read_sql("SELECT * FROM tickets", conn)

    if not df.empty:
        # Display Ticket List
        df = df[["id", "date", "batch_name", "ticket_number", "status", "type"]]
        st.dataframe(df)

        # Select Ticket to Resolve or Delete
        ticket_id = st.number_input("Enter Ticket ID to Update:", min_value=1, step=1)

        action = st.radio("Action:", ["Resolve", "Delete"])

        if st.button("Update Ticket"):
            if action == "Resolve":
                cursor.execute("UPDATE tickets SET status = 'Resolved' WHERE id = ?", (ticket_id,))
                conn.commit()
                st.success(f"✅ Ticket ID {ticket_id} marked as Resolved.")
            elif action == "Delete":
                cursor.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
                conn.commit()
                st.warning(f"🗑 Ticket ID {ticket_id} has been deleted.")

    else:
        st.info("ℹ️ No tickets available.")

# Close Database Connection
conn.close()
