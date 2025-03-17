import streamlit as st
import sqlite3
import pandas as pd
import datetime
import io

# --- Database Connection ---
@st.cache_resource
def get_db_connection():
    conn = sqlite3.connect("ticket_management.db", check_same_thread=False)
    return conn

conn = get_db_connection()
cursor = conn.cursor()

# --- Create the Tickets Table ---
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
    pay REAL DEFAULT 5.5
)
''')
conn.commit()

# --- Ensure Schema Compatibility ---
cursor.execute("PRAGMA table_info(tickets)")
columns_info = cursor.fetchall()
column_names = [col[1] for col in columns_info]
if "pay" not in column_names:
    cursor.execute("ALTER TABLE tickets ADD COLUMN pay REAL DEFAULT 5.5")
    conn.commit()
if "num_sub_tickets" not in column_names:
    cursor.execute("ALTER TABLE tickets ADD COLUMN num_sub_tickets INTEGER DEFAULT 1")
    conn.commit()

# --- Sidebar Navigation ---
st.sidebar.title("Ticket Management App")
st.sidebar.info("Select a page from the menu below.")
menu = st.sidebar.radio("Menu", ["Add Intake Tickets", "Add Return Tickets", "Manage Tickets", "Dashboard"])

# --- Function to Add Tickets ---
def add_tickets(ticket_category):
    st.header(f"Add {ticket_category} Tickets")
    st.markdown(
        """
        **Instructions:**
        - **General Ticket:** Enter multiple ticket numbers separated by a space. Each ticket is added as a single entry.
        - **Large Ticket:** Enter one ticket number and specify the number of sub-tickets.
        """
    )
    ticket_entry_type = st.radio(
        "Select Ticket Entry Type", 
        ["General Ticket", "Large Ticket"],
        index=0,
        help="Choose how to add your tickets."
    )
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    
    # Generate a new batch name based on the number of distinct batches.
    cursor.execute("SELECT COUNT(DISTINCT batch_name) FROM tickets")
    batch_count = cursor.fetchone()[0] + 1
    batch_name = f"Batch-{batch_count}"
    
    if ticket_entry_type == "General Ticket":
        ticket_numbers_input = st.text_input(
            "Enter Ticket Numbers (separated by space):", 
            help="Example: 12345 12346 12347"
        )
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
                    st.balloons()
            else:
                st.error("Please enter at least one ticket number.")
                    
    elif ticket_entry_type == "Large Ticket":
        large_ticket_number = st.text_input(
            "Enter Large Ticket Number:", 
            help="This ticket represents a group of sub-tickets."
        )
        num_sub_tickets = st.number_input(
            "Number of Sub-Tickets", 
            min_value=1, step=1, value=1,
            help="Enter the number of sub-tickets to include."
        )
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
                    st.balloons()
                except sqlite3.IntegrityError:
                    st.error("Ticket number already exists.")
            else:
                st.error("Please enter a valid ticket number.")

# --- Page: Add Intake Tickets ---
if menu == "Add Intake Tickets":
    add_tickets("Intake")

# --- Page: Add Return Tickets ---
elif menu == "Add Return Tickets":
    add_tickets("Return")

# --- Page: Manage Tickets ---
elif menu == "Manage Tickets":
    st.header("Manage Tickets")
    st.markdown("Use the search box below to filter tickets by ticket number or batch name.")
    search_query = st.text_input("Search Tickets", help="Enter ticket number or batch name to filter results.")
    if search_query:
        query = "SELECT * FROM tickets WHERE ticket_number LIKE ? OR batch_name LIKE ?"
        params = (f"%{search_query}%", f"%{search_query}%")
        df = pd.read_sql(query, conn, params=params)
    else:
        df = pd.read_sql("SELECT * FROM tickets", conn)
    
    st.dataframe(df)
    
    with st.expander("Resolve a Ticket"):
        ticket_to_resolve = st.text_input("Enter Ticket Number to Resolve", help="Enter the exact ticket number to mark as resolved.")
        if st.button("Resolve Ticket"):
            ticket_to_resolve = ticket_to_resolve.strip()
            if ticket_to_resolve:
                cursor.execute("UPDATE tickets SET status='Resolved' WHERE ticket_number=?", (ticket_to_resolve,))
                conn.commit()
                st.success(f"Ticket '{ticket_to_resolve}' resolved.")
            else:
                st.error("Please enter a valid ticket number.")
    st.info("Tip: Use the search box above to quickly locate tickets before resolving them.")

# --- Page: Dashboard ---
elif menu == "Dashboard":
    st.header("Dashboard")
    df = pd.read_sql("SELECT * FROM tickets", conn)
    # Ensure columns "pay" and "num_sub_tickets" exist, else add default values.
    if "pay" not in df.columns:
        df["pay"] = 5.5
    if "num_sub_tickets" not in df.columns:
        df["num_sub_tickets"] = 1
    total_tickets = df.shape[0]
    unresolved_tickets = df[df["status"] == "Open"].shape[0]
    resolved_tickets = df[df["status"] == "Resolved"].shape[0]
    total_pay = (df["pay"] * df["num_sub_tickets"]).sum()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Tickets", total_tickets)
    col2.metric("Resolved Tickets", resolved_tickets)
    col3.metric("Unresolved Tickets", unresolved_tickets)
    col4.metric("Total Pay", f"${total_pay:.2f}")
    
    st.markdown("### All Ticket Records")
    st.dataframe(df)
    
    # Provide option to download data as CSV.
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Tickets as CSV",
        data=csv,
        file_name='tickets.csv',
        mime='text/csv'
    )
    st.info("Review the dashboard metrics and download the CSV for further analysis.")
