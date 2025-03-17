import streamlit as st
import sqlite3
import pandas as pd
import datetime

# Database Setup
conn = sqlite3.connect("ticket_management.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    time TEXT,
                    batch_name TEXT,
                    ticket_number TEXT UNIQUE,
                    status TEXT,
                    type TEXT,
                    pay_per_ticket REAL
                )''')
conn.commit()

# Get Current Date & Time
current_date = datetime.datetime.now().strftime("%Y-%m-%d")
current_time = datetime.datetime.now().strftime("%H:%M:%S")
weekday = datetime.datetime.now().strftime("%A")

# Get Current Batch
cursor.execute("SELECT COUNT(*) FROM tickets WHERE date = ?", (current_date,))
batch_number = cursor.fetchone()[0] + 1
batch_name = f"{weekday} Batch {batch_number}"

# Sidebar Menu
st.sidebar.title("📋 Ticket Management")
menu = st.sidebar.radio("Navigation", ["➕ Add Tickets", "📊 Dashboard", "🗂 Manage Tickets", "✅ Resolve Tickets"])

# **➕ Paste New Tickets**
if menu == "➕ Add Tickets":
    st.title("➕ Add Tickets (Intake/Outgoing)")

    ticket_numbers = st.text_area("Paste Ticket Numbers (comma-separated):", placeholder="E.g., 1234, 5678, 91011")
    ticket_type = st.radio("Ticket Type:", ["Intake", "Outgoing"])
    pay_per_ticket = st.number_input("Pay Per Ticket ($):", min_value=0.0, value=5.0, step=0.5)

    if st.button("Save Tickets"):
        ticket_list = [t.strip() for t in ticket_numbers.split(",") if t.strip()]
        if ticket_list:
            added_count = 0
            for ticket in ticket_list:
                try:
                    cursor.execute("INSERT INTO tickets (date, time, batch_name, ticket_number, status, type, pay_per_ticket) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                   (current_date, current_time, batch_name, ticket, "Unresolved", ticket_type.lower(), pay_per_ticket))
                    added_count += 1
                except sqlite3.IntegrityError:
                    pass  # Ignore duplicate ticket entries
            conn.commit()
            st.success(f"✅ {added_count} tickets added to '{batch_name}'!")
        else:
            st.error("⚠️ Enter at least one ticket.")

# **📊 Dashboard & Analytics**
elif menu == "📊 Dashboard":
    st.title("📊 Ticket Analytics Dashboard")
    df = pd.read_sql("SELECT * FROM tickets", conn)

    if not df.empty:
        df["Total Pay"] = df["pay_per_ticket"]
        total_tickets = len(df)
        unresolved_tickets = len(df[df["status"] == "Unresolved"])
        resolved_tickets = len(df[df["status"] == "Resolved"])
        total_earnings = df["Total Pay"].sum()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🎟 Total Tickets", total_tickets)
        col2.metric("⏳ Unresolved Tickets", unresolved_tickets)
        col3.metric("✅ Resolved Tickets", resolved_tickets)
        col4.metric("💰 Earnings", f"${total_earnings:.2f}")

        st.write("### 📦 Tickets by Type")
        ticket_summary = df.groupby("type").agg({"ticket_number": "count"})
        st.bar_chart(ticket_summary)

        st.write("### 🏅 Batch Breakdown")
        batch_summary = df.groupby("batch_name").agg({"ticket_number": "count"})
        st.bar_chart(batch_summary)
    else:
        st.info("ℹ️ No tickets available. Add some first.")

# **🗂 Manage Tickets (Copy, Delete, Filter)**
elif menu == "🗂 Manage Tickets":
    st.title("🗂 Manage Tickets")

    df = pd.read_sql("SELECT * FROM tickets", conn)

    if not df.empty:
        df = df[["id", "date", "batch_name", "ticket_number", "status", "type"]]
        st.dataframe(df)

        # **Copy Ticket Numbers**
        st.write("### 📋 Copy Ticket Numbers")
        selected_tickets = st.multiselect("Select Tickets:", df["ticket_number"])
        if selected_tickets:
            ticket_str = ", ".join(selected_tickets)
            st.text_area("Copy these tickets:", ticket_str)

        # **Update/Delete Tickets**
        ticket_id = st.number_input("Enter Ticket ID:", min_value=1, step=1)
        action = st.radio("Action:", ["Resolve", "Delete"])

        if st.button("Update Ticket"):
            if action == "Resolve":
                cursor.execute("UPDATE tickets SET status = 'Resolved' WHERE id = ?", (ticket_id,))
                conn.commit()
                st.success(f"✅ Ticket ID {ticket_id} marked as Resolved.")
            elif action == "Delete":
                cursor.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
                conn.commit()
                st.warning(f"🗑 Ticket ID {ticket_id} deleted.")

    else:
        st.info("ℹ️ No tickets available.")

# **✅ Bulk Resolve Tickets**
elif menu == "✅ Resolve Tickets":
    st.title("✅ Bulk Resolve Tickets")

    resolved_tickets = st.text_area("Paste Ticket Numbers (comma-separated):", placeholder="E.g., 1234, 5678, 91011")

    if st.button("Mark as Resolved"):
        ticket_list = [t.strip() for t in resolved_tickets.split(",") if t.strip()]
        if ticket_list:
            updated_count = 0
            for ticket in ticket_list:
                cursor.execute("UPDATE tickets SET status = 'Resolved' WHERE ticket_number = ?", (ticket,))
                if cursor.rowcount > 0:
                    updated_count += 1
            conn.commit()
            st.success(f"✅ {updated_count} tickets marked as Resolved!")
        else:
            st.error("⚠️ Enter at least one ticket number.")

# Close Database Connection
conn.close()
