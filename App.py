import streamlit as st
import sqlite3
import pandas as pd

# Cache the database connection as a resource (persist across reruns & sessions)
@st.cache_resource
def get_db_connection():
    # Use check_same_thread=False to allow reuse of the connection in other threads (for SQLite)
    conn = sqlite3.connect('data.db', check_same_thread=False)
    return conn

# Initialize connection (this will use cache after first run)
conn = get_db_connection()
cur = conn.cursor()
# Ensure required tables exist
cur.execute("CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, password TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS tickets(id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT)")
conn.commit()

# User Authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        # Verify credentials against users table
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user_record = cur.fetchone()
        if user_record:
            st.session_state.authenticated = True
            st.success("Logged in successfully!")
        else:
            st.error("Invalid username or password. Please try again.")
    st.stop()  # Stop here if not authenticated

# If authenticated, show the ticket entry interface
st.title("Ticket Submission Portal")

# General Ticket Entry (space-separated tickets)
st.subheader("General Ticket Entry")
ticket_input = st.text_input("Enter one or multiple ticket IDs (separated by spaces)")
if st.button("Add Tickets"):
    if ticket_input.strip():
        # Split by any whitespace and filter out empty strings
        tickets = [t for t in ticket_input.split() if t]
        if tickets:
            # Insert all tickets in one batch
            cur.executemany("INSERT INTO tickets(content) VALUES(?)", [(t,) for t in tickets])
            conn.commit()
            st.success(f"Added {len(tickets)} tickets: " + ", ".join(tickets))
        else:
            st.warning("No valid tickets found in input.")
    else:
        st.warning("Please enter at least one ticket ID.")

# Large Ticket Entry (multiple sub-tickets via text area)
st.subheader("Large Ticket Entry")
multi_input = st.text_area("Enter multiple tickets (one per line)")
if st.button("Add Multiple Tickets"):
    if multi_input.strip():
        # Split by lines and filter out empty lines
        tickets = [line.strip() for line in multi_input.splitlines() if line.strip()]
        if tickets:
            cur.executemany("INSERT INTO tickets(content) VALUES(?)", [(t,) for t in tickets])
            conn.commit()
            st.success(f"Added {len(tickets)} tickets from the list.")
        else:
            st.warning("No valid tickets found (please enter one per line).")
    else:
        st.warning("The input is empty. Please enter ticket IDs, one per line.")

# (Optional) Display all tickets for verification
st.subheader("Current Tickets in Database")
ticket_df = pd.read_sql_query("SELECT * FROM tickets", conn)
st.dataframe(ticket_df)
