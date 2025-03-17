import streamlit as st
import sqlite3
import pandas as pd
import datetime
import plotly.express as px

# ---------------------
# Configurable Settings
# ---------------------
if "ticket_price" not in st.session_state:
    st.session_state.ticket_price = 5.5

# ---------------------
# Database Connection
# ---------------------
@st.cache_resource
def get_db_connection():
    conn = sqlite3.connect("ticket_management.db", check_same_thread=False)
    return conn

conn = get_db_connection()
cursor = conn.cursor()

# ---------------------
# Create Tickets Table
# ---------------------
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

# Ensure schema compatibility
cursor.execute("PRAGMA table_info(tickets)")
columns_info = cursor.fetchall()
column_names = [col[1] for col in columns_info]
if "pay" not in column_names:
    cursor.execute("ALTER TABLE tickets ADD COLUMN pay REAL DEFAULT 5.5")
    conn.commit()
if "num_sub_tickets" not in column_names:
    cursor.execute("ALTER TABLE tickets ADD COLUMN num_sub_tickets INTEGER DEFAULT 1")
    conn.commit()

# ---------------------
# Sidebar Navigation
# ---------------------
st.sidebar.title("Ticket Management App")
st.sidebar.markdown("### Navigation")
menu = st.sidebar.radio("Go to", 
                        ["Add Intake Tickets", "Add Return Tickets", "Manage Tickets", "Dashboard", "Settings"])

# ---------------------
# Function to Add Tickets
# ---------------------
def add_tickets(ticket_category):
    st.header(f"Add {ticket_category} Tickets")
    st.markdown(
        """
        **Instructions:**
        - **General Ticket:** Paste or type multiple ticket numbers separated by any whitespace (spaces, tabs, or newlines).
        - **Large Ticket:** Enter one ticket number and specify the number of sub-tickets.
        """
    )
    ticket_entry_type = st.radio("Select Ticket Entry Type", 
                                 ["General Ticket", "Large Ticket"],
                                 index=0,
                                 help="Choose how to add your tickets.")
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    
    # Generate a new batch name based on distinct batches in the database.
    cursor.execute("SELECT COUNT(DISTINCT batch_name) FROM tickets")
    batch_count = cursor.fetchone()[0] + 1
    batch_name = f"Batch-{batch_count}"
    
    if ticket_entry_type == "General Ticket":
        ticket_input = st.text_area("Enter Ticket Numbers", 
                                    height=150, 
                                    help="Separate ticket numbers with any whitespace. Example: 12345 12346 12347 or one per line")
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
                                "INSERT INTO tickets (date, time, batch_name, ticket_number, num_sub_tickets, type, pay) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (current_date, current_time, batch_name, tn, 1, ticket_category, st.session_state.ticket_price)
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
                        "INSERT INTO tickets (date, time, batch_name, ticket_number, num_sub_tickets, type, pay) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (current_date, current_time, batch_name, large_ticket, sub_ticket_count, ticket_category, st.session_state.ticket_price)
                    )
                    conn.commit()
                    st.success(f"Successfully added large ticket '{large_ticket}' with {sub_ticket_count} sub-tickets for {ticket_category}.")
                    st.balloons()
                except sqlite3.IntegrityError:
                    st.error("Ticket number already exists.")
            else:
                st.error("Please enter a valid ticket number.")

# ---------------------
# Page: Add Intake Tickets
# ---------------------
if menu == "Add Intake Tickets":
    add_tickets("Intake")

# ---------------------
# Page: Add Return Tickets
# ---------------------
elif menu == "Add Return Tickets":
    add_tickets("Return")

# ---------------------
# Page: Manage Tickets (Advanced Filtering & Pagination)
# ---------------------
elif menu == "Manage Tickets":
    st.header("Manage Tickets")
    st.markdown("Filter tickets using the options below:")

    # Advanced Filtering Options
    start_date = st.sidebar.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
    end_date = st.sidebar.date_input("End Date", datetime.date.today())
    status_filter = st.sidebar.selectbox("Status", ["All", "Open", "Resolved"])
    search_term = st.sidebar.text_input("Search", help="Search by ticket number or batch name")
    
    query = "SELECT * FROM tickets WHERE date BETWEEN ? AND ?"
    params = [start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")]
    
    if status_filter != "All":
        query += " AND status = ?"
        params.append(status_filter)
    if search_term:
        query += " AND (ticket_number LIKE ? OR batch_name LIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])
    
    df_filtered = pd.read_sql(query, conn, params=params)
    
    # Pagination Controls
    page_size = st.sidebar.number_input("Page Size", min_value=5, value=10, step=5)
    page_number = st.sidebar.number_input("Page Number", min_value=1, value=1, step=1)
    total_tickets = df_filtered.shape[0]
    start_index = (page_number - 1) * page_size
    end_index = start_index + page_size
    paginated_df = df_filtered.iloc[start_index:end_index]
    
    st.write(f"Displaying tickets {start_index+1} to {min(end_index, total_tickets)} of {total_tickets}")
    st.dataframe(paginated_df)
    
    # Expander for Resolve and Delete Options
    with st.expander("Resolve a Ticket"):
        ticket_to_resolve = st.text_input("Ticket Number to Resolve", key="resolve")
        if st.button("Resolve Ticket"):
            ticket_to_resolve = ticket_to_resolve.strip()
            if ticket_to_resolve:
                cursor.execute("UPDATE tickets SET status='Resolved' WHERE ticket_number=?", (ticket_to_resolve,))
                conn.commit()
                st.success(f"Ticket '{ticket_to_resolve}' marked as Resolved.")
            else:
                st.error("Enter a valid ticket number.")
    with st.expander("Delete a Ticket"):
        ticket_to_delete = st.text_input("Ticket Number to Delete", key="delete")
        if st.button("Delete Ticket"):
            ticket_to_delete = ticket_to_delete.strip()
            if ticket_to_delete:
                cursor.execute("DELETE FROM tickets WHERE ticket_number=?", (ticket_to_delete,))
                conn.commit()
                st.success(f"Ticket '{ticket_to_delete}' deleted.")
            else:
                st.error("Enter a valid ticket number.")

# ---------------------
# Page: Dashboard (Interactive Analytics)
# ---------------------
elif menu == "Dashboard":
    st.header("Dashboard Analytics")
    df = pd.read_sql("SELECT * FROM tickets", conn)
    if "pay" not in df.columns:
        df["pay"] = st.session_state.ticket_price
    if "num_sub_tickets" not in df.columns:
        df["num_sub_tickets"] = 1
    
    # Metrics
    total_tickets = df.shape[0]
    unresolved_tickets = df[df["status"] == "Open"].shape[0]
    resolved_tickets = df[df["status"] == "Resolved"].shape[0]
    total_pay = (df["pay"] * df["num_sub_tickets"]).sum()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Tickets", total_tickets)
    col2.metric("Resolved Tickets", resolved_tickets)
    col3.metric("Unresolved Tickets", unresolved_tickets)
    col4.metric("Total Pay", f"${total_pay:.2f}")
    
    st.markdown("### Ticket Records")
    st.dataframe(df)
    
    st.markdown("### Interactive Analytics")
    # Bar Chart: Ticket Count by Status
    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]
    fig1 = px.bar(status_counts, x="status", y="count", color="status", title="Ticket Count by Status")
    st.plotly_chart(fig1, use_container_width=True)
    
    # Bar Chart: Ticket Count by Category
    type_counts = df["type"].value_counts().reset_index()
    type_counts.columns = ["type", "count"]
    fig2 = px.bar(type_counts, x="type", y="count", color="type", title="Ticket Count by Category")
    st.plotly_chart(fig2, use_container_width=True)
    
    # Pie Chart: Ticket Status Distribution
    fig3 = px.pie(status_counts, names="status", values="count", title="Ticket Status Distribution")
    st.plotly_chart(fig3, use_container_width=True)
    
    # Line Chart: Tickets Over Time
    try:
        df["date"] = pd.to_datetime(df["date"])
        tickets_over_time = df.groupby("date").size().reset_index(name="count")
        fig4 = px.line(tickets_over_time, x="date", y="count", title="Tickets Over Time")
        st.plotly_chart(fig4, use_container_width=True)
    except Exception as e:
        st.error("Error generating time series chart: " + str(e))
    
    # CSV Download Option
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Tickets as CSV", data=csv, file_name="tickets.csv", mime="text/csv")

# ---------------------
# Page: Settings (Configurable Settings)
# ---------------------
elif menu == "Settings":
    st.header("Application Settings")
    st.markdown("Adjust the global settings for your ticket management app below.")
    
    ticket_price = st.number_input("Fixed Ticket Price", min_value=0.0, value=st.session_state.ticket_price, step=0.5)
    st.session_state.ticket_price = ticket_price
    st.success("Settings updated!")
    st.markdown("All new tickets will use the updated ticket price.")
