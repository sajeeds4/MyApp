import streamlit as st
import sqlite3
import pandas as pd
import datetime

# Database Setup
conn = sqlite3.connect("tickets.db", check_same_thread=False)
cursor = conn.cursor()

# Create Table if Not Exists
cursor.execute('''CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    time TEXT,
                    batch_name TEXT,
                    tickets TEXT,
                    ticket_count INTEGER,
                    pay_per_ticket REAL
                )''')
conn.commit()

# Streamlit UI
st.title("🎟 Ticket Manager & Earnings Dashboard")

# Get Current Date, Time, and Weekday
current_date = datetime.datetime.now().strftime("%Y-%m-%d")
current_time = datetime.datetime.now().strftime("%H:%M:%S")
weekday = datetime.datetime.now().strftime("%A")  # Monday, Tuesday, etc.

# Get Current Batch Number
cursor.execute("SELECT COUNT(*) FROM tickets WHERE date = ?", (current_date,))
batch_number = cursor.fetchone()[0] + 1  # Increment for next batch

batch_name = f"{weekday} Batch {batch_number}"

# User Input
tickets_input = st.text_area("Enter Tickets (comma-separated):", placeholder="E.g., 1234, 5678, 91011")

pay_per_ticket = st.number_input("Enter Pay Per Ticket ($):", min_value=0.0, value=5.0, step=0.5)

# Save Tickets
if st.button("Save Tickets"):
    ticket_list = [t.strip() for t in tickets_input.split(",") if t.strip()]
    ticket_count = len(ticket_list)

    if ticket_count > 0:
        cursor.execute("INSERT INTO tickets (date, time, batch_name, tickets, ticket_count, pay_per_ticket) VALUES (?, ?, ?, ?, ?, ?)",
                       (current_date, current_time, batch_name, ", ".join(ticket_list), ticket_count, pay_per_ticket))
        conn.commit()
        st.success(f"✅ Saved {ticket_count} tickets under '{batch_name}'!")
    else:
        st.error("⚠️ No valid tickets entered. Please add at least one ticket.")

# Dashboard Analytics
st.subheader("📊 Earnings & Batch Analytics")

df = pd.read_sql("SELECT * FROM tickets", conn)

if not df.empty:
    df["Total Pay"] = df["ticket_count"] * df["pay_per_ticket"]

    # Display Batch History
    st.write("### 🏆 Batch History")
    st.dataframe(df[["date", "time", "batch_name", "ticket_count", "Total Pay"]])

    # Key Metrics
    total_tickets = df["ticket_count"].sum()
    total_earnings = df["Total Pay"].sum()

    col1, col2 = st.columns(2)
    col1.metric("🎫 Total Tickets Processed", total_tickets)
    col2.metric("💰 Total Earnings", f"${total_earnings:.2f}")

    # Daily Summary
    st.write("### 📅 Daily Summary")
    daily_summary = df.groupby("date").agg({"ticket_count": "sum", "Total Pay": "sum"})
    st.bar_chart(daily_summary)

    # Batch Breakdown
    st.write("### 🏅 Batch Breakdown")
    batch_summary = df.groupby("batch_name").agg({"ticket_count": "sum", "Total Pay": "sum"})
    st.bar_chart(batch_summary)

else:
    st.info("ℹ️ No ticket data available. Enter tickets to see analytics.")

# Close Database Connection
conn.close()
