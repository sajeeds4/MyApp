import streamlit as st
import sqlite3
import pandas as pd
import datetime
import plotly.express as px
from io import BytesIO

# -----------------------------------------------------------
# Page Configuration & Custom CSS for a Fully Graphical UI
# -----------------------------------------------------------
st.set_page_config(
    page_title="Ticket Management Dashboard",
    page_icon=":ticket:",
    layout="wide"
)

# Custom CSS to enhance the look (light mode)
st.markdown(
    """
    <style>
    /* Global styling */
    body {
        background-color: #f5f5f5;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #333;
    }
    /* Container styling for main content */
    .reportview-container .main .block-container {
        padding-top: 2rem;
        padding-right: 2rem;
        padding-left: 2rem;
        padding-bottom: 2rem;
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0 0 15px rgba(0, 0, 0, 0.1);
    }
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #ffffff;
    }
    /* Header banner */
    .header-banner {
        background-image: url('https://via.placeholder.com/1500x200.png?text=Your+Business+Tagline');
        background-size: cover;
        background-position: center;
        border-radius: 10px;
        margin-bottom: 1rem;
        padding: 2rem;
        text-align: center;
        color: #ffffff;
    }
    .header-banner h1 {
        font-size: 3rem;
        font-weight: bold;
    }
    /* KPI card styling (using Streamlit metric style) */
    .stMetric {
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0 0 8px rgba(0,0,0,0.1);
    }
    /* DataFrame styling */
    .dataframe th {
        background-color: #f0f0f0;
        color: #333;
    }
    /* Footer styling */
    .footer {
        text-align: center;
        font-size: 0.8rem;
        padding: 1rem;
        color: #777;
    }
    </style>
    """, unsafe_allow_html=True
)

# -----------------------------------------------------------
# Top Banner (Logo and Tagline)
# -----------------------------------------------------------
st.markdown(
    """
    <div class="header-banner">
        <h1>Ticket Management Dashboard</h1>
        <p>Your Business: Resolve tickets at $5.5 each for consistent earnings</p>
    </div>
    """, unsafe_allow_html=True
)

# -----------------------------------------------------------
# Configurable Settings (stored in session state)
# -----------------------------------------------------------
if "ticket_price" not in st.session_state:
    st.session_state.ticket_price = 5.5

# -----------------------------------------------------------
# Database Connection (cached)
# -----------------------------------------------------------
@st.cache_resource
def get_db_connection():
    conn = sqlite3.connect("ticket_management.db", check_same_thread=False)
    return conn

conn = get_db_connection()
cursor = conn.cursor()

# -----------------------------------------------------------
# Create Tickets Table (with additional 'comments' field)
# -----------------------------------------------------------
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
    pay REAL DEFAULT 5.5,
    comments TEXT DEFAULT ''
)
''')
conn.commit()

# Ensure schema compatibility for 'pay', 'num_sub_tickets', and 'comments'
cursor.execute("PRAGMA table_info(tickets)")
columns_info = cursor.fetchall()
column_names = [col[1] for col in columns_info]
if "pay" not in column_names:
    cursor.execute("ALTER TABLE tickets ADD COLUMN pay REAL DEFAULT 5.5")
    conn.commit()
if "num_sub_tickets" not in column_names:
    cursor.execute("ALTER TABLE tickets ADD COLUMN num_sub_tickets INTEGER DEFAULT 1")
    conn.commit()
if "comments" not in column_names:
    cursor.execute("ALTER TABLE tickets ADD COLUMN comments TEXT DEFAULT ''")
    conn.commit()

# -----------------------------------------------------------
# Sidebar Navigation (with icons)
# -----------------------------------------------------------
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to", 
                        ["Add Intake Tickets", "Add Return Tickets", "Manage Tickets", "Dashboard", "Settings"],
                        index=0)

# -----------------------------------------------------------
# Function: Add Tickets (for Intake or Return)
# -----------------------------------------------------------
def add_tickets(ticket_category):
    st.header(f"Add {ticket_category} Tickets")
    st.markdown(
        """
        **Instructions:**
        - **General Ticket:** Paste or type multiple ticket numbers separated by any whitespace (space, tab, newline).
        - **Large Ticket:** Enter one ticket number and specify the number of sub-tickets.
        """
    )
    ticket_entry_type = st.radio("Select Ticket Entry Type", 
                                 ["General Ticket", "Large Ticket"],
                                 index=0,
                                 help="Choose how to add your tickets.")
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    
    # Generate a new batch name based on distinct batches count
    cursor.execute("SELECT COUNT(DISTINCT batch_name) FROM tickets")
    batch_count = cursor.fetchone()[0] + 1
    batch_name = f"Batch-{batch_count}"
    
    if ticket_entry_type == "General Ticket":
        ticket_input = st.text_area("Enter Ticket Numbers", 
                                    height=150, 
                                    help="Separate ticket numbers with whitespace. Example: 12345 12346 12347 or one per line")
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

# -----------------------------------------------------------
# Page: Add Intake Tickets
# -----------------------------------------------------------
if menu == "Add Intake Tickets":
    add_tickets("Intake")

# -----------------------------------------------------------
# Page: Add Return Tickets
# -----------------------------------------------------------
elif menu == "Add Return Tickets":
    add_tickets("Return")

# -----------------------------------------------------------
# Page: Manage Tickets (Advanced Filtering, Sorting, Pagination, Editing)
# -----------------------------------------------------------
elif menu == "Manage Tickets":
    st.header("Manage Tickets")
    st.markdown("Use the filters below to locate and manage your tickets:")
    
    col1, col2, col3, col4 = st.columns(4)
    start_date = col1.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
    end_date = col2.date_input("End Date", datetime.date.today())
    status_filter = col3.selectbox("Status", ["All", "Open", "Resolved"])
    type_filter = col4.selectbox("Ticket Type", ["All", "Intake", "Return"])
    
    search_term = st.text_input("Search", help="Search by ticket number or batch name")
    
    query = "SELECT * FROM tickets WHERE date BETWEEN ? AND ?"
    params = [start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")]
    if status_filter != "All":
        query += " AND status = ?"
        params.append(status_filter)
    if type_filter != "All":
        query += " AND type = ?"
        params.append(type_filter)
    if search_term:
        query += " AND (ticket_number LIKE ? OR batch_name LIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])
    
    order_by = st.selectbox("Sort By", ["date", "ticket_number", "status", "type"], index=0)
    query += f" ORDER BY {order_by} DESC"
    
    df_filtered = pd.read_sql(query, conn, params=params)
    
    # Pagination Controls
    page_size = st.number_input("Page Size", min_value=5, value=10, step=5)
    page_number = st.number_input("Page Number", min_value=1, value=1, step=1)
    total_tickets = df_filtered.shape[0]
    start_index = (page_number - 1) * page_size
    end_index = start_index + page_size
    paginated_df = df_filtered.iloc[start_index:end_index]
    
    st.write(f"Showing tickets {start_index+1} to {min(end_index, total_tickets)} of {total_tickets}")
    st.dataframe(paginated_df)
    
    # Ticket Editing Section
    with st.expander("Edit Ticket Details"):
        ticket_to_edit = st.text_input("Enter Ticket Number to Edit", key="edit_ticket")
        if st.button("Load Ticket"):
            ticket_to_edit = ticket_to_edit.strip()
            if ticket_to_edit:
                cursor.execute("SELECT * FROM tickets WHERE ticket_number=?", (ticket_to_edit,))
                ticket_data = cursor.fetchone()
                if ticket_data:
                    cols = [column[0] for column in cursor.description]
                    ticket_dict = dict(zip(cols, ticket_data))
                    st.write("Current Ticket Details:")
                    st.json(ticket_dict)
                    
                    new_status = st.selectbox("Update Status", ["Open", "Resolved"], index=0 if ticket_dict["status"]=="Open" else 1)
                    new_comments = st.text_area("Comments", value=ticket_dict.get("comments", ""))
                    
                    if st.button("Update Ticket"):
                        cursor.execute("UPDATE tickets SET status=?, comments=? WHERE ticket_number=?",
                                       (new_status, new_comments, ticket_to_edit))
                        conn.commit()
                        st.success("Ticket updated successfully!")
                else:
                    st.error("Ticket not found.")
            else:
                st.error("Please enter a valid ticket number.")
    
    # Expanders for Resolving & Deleting Tickets
    with st.expander("Resolve a Ticket"):
        ticket_to_resolve = st.text_input("Ticket Number to Resolve", key="resolve", help="Enter the exact ticket number.")
        if st.button("Resolve Ticket"):
            ticket_to_resolve = ticket_to_resolve.strip()
            if ticket_to_resolve:
                cursor.execute("UPDATE tickets SET status='Resolved' WHERE ticket_number=?", (ticket_to_resolve,))
                conn.commit()
                st.success(f"Ticket '{ticket_to_resolve}' marked as Resolved.")
            else:
                st.error("Enter a valid ticket number.")
    with st.expander("Delete a Ticket"):
        ticket_to_delete = st.text_input("Ticket Number to Delete", key="delete", help="Enter the exact ticket number.")
        if st.button("Delete Ticket"):
            ticket_to_delete = ticket_to_delete.strip()
            if ticket_to_delete:
                cursor.execute("DELETE FROM tickets WHERE ticket_number=?", (ticket_to_delete,))
                conn.commit()
                st.success(f"Ticket '{ticket_to_delete}' deleted.")
            else:
                st.error("Enter a valid ticket number.")
    
    st.info("Use the filters and actions above to efficiently manage your tickets.")

# -----------------------------------------------------------
# Page: Dashboard (Fully Graphical, Interactive Analytics & Business Insights)
# -----------------------------------------------------------
elif menu == "Dashboard":
    st.header("Dashboard Analytics")
    df = pd.read_sql("SELECT * FROM tickets", conn)
    if "pay" not in df.columns:
        df["pay"] = st.session_state.ticket_price
    if "num_sub_tickets" not in df.columns:
        df["num_sub_tickets"] = 1

    # Calculate separate earnings
    intake_df = df[df["type"] == "Intake"]
    return_df = df[df["type"] == "Return"]
    estimated_earning = (intake_df["pay"] * intake_df["num_sub_tickets"]).sum()
    actual_earning = (return_df["pay"] * return_df["num_sub_tickets"]).sum()
    
    total_tickets = df.shape[0]
    unresolved_tickets = df[df["status"] == "Open"].shape[0]
    resolved_tickets = df[df["status"] == "Resolved"].shape[0]
    
    # Display KPI Cards
    kpi_cols = st.columns(5)
    kpi_cols[0].metric("Total Tickets", total_tickets)
    kpi_cols[1].metric("Resolved Tickets", resolved_tickets)
    kpi_cols[2].metric("Unresolved Tickets", unresolved_tickets)
    kpi_cols[3].metric("Estimated Earnings (Intake)", f"${estimated_earning:.2f}")
    kpi_cols[4].metric("Actual Earnings (Return)", f"${actual_earning:.2f}")
    
    st.markdown("### Ticket Data Overview")
    st.dataframe(df.style.format({"pay": "${:,.2f}"}))
    
    st.markdown("### Interactive Charts")
    # Bar Chart: Ticket Count by Status
    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]
    fig1 = px.bar(status_counts, x="status", y="count", color="status", title="Ticket Count by Status",
                  template="plotly_white")
    st.plotly_chart(fig1, use_container_width=True)
    
    # Bar Chart: Ticket Count by Category
    type_counts = df["type"].value_counts().reset_index()
    type_counts.columns = ["type", "count"]
    fig2 = px.bar(type_counts, x="type", y="count", color="type", title="Ticket Count by Category",
                  template="plotly_white")
    st.plotly_chart(fig2, use_container_width=True)
    
    # Pie Chart: Ticket Status Distribution
    fig3 = px.pie(status_counts, names="status", values="count", title="Ticket Status Distribution",
                  template="plotly_white")
    st.plotly_chart(fig3, use_container_width=True)
    
    # Line Chart: Tickets Over Time
    try:
        df["date"] = pd.to_datetime(df["date"])
        tickets_over_time = df.groupby("date").size().reset_index(name="count")
        fig4 = px.line(tickets_over_time, x="date", y="count", title="Tickets Over Time",
                       template="plotly_white")
        st.plotly_chart(fig4, use_container_width=True)
    except Exception as e:
        st.error("Error generating time series chart: " + str(e))
    
    # Business Insights Section
    st.markdown("### Business Insights")
    completion_rate = (resolved_tickets / total_tickets * 100) if total_tickets else 0
    st.markdown(f"**Overall Ticket Completion Rate:** {completion_rate:.1f}%")
    
    # Identify the top performing batch (by count of tickets)
    top_batch = df['batch_name'].value_counts().idxmax() if total_tickets > 0 else "N/A"
    st.markdown(f"**Top Performing Batch:** {top_batch}")
    
    # Weekly Revenue Trend (if enough data exists)
    try:
        df["date"] = pd.to_datetime(df["date"])
        weekly = df.groupby(pd.Grouper(key="date", freq="W")).size().reset_index(name="tickets")
        fig5 = px.line(weekly, x="date", y="tickets", title="Weekly Ticket Trend", template="plotly_white")
        st.plotly_chart(fig5, use_container_width=True)
    except Exception as e:
        st.error("Error generating weekly trend chart: " + str(e))
    
    # Export Options
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Tickets as CSV", data=csv, file_name="tickets.csv", mime="text/csv")
    
    towrite = BytesIO()
    df.to_excel(towrite, index=False, sheet_name="Tickets")
    towrite.seek(0)
    st.download_button("Download Tickets as Excel", data=towrite, file_name="tickets.xlsx", mime="application/vnd.ms-excel")
    
    st.info("Review the charts and insights above for a complete view of your ticket operations and earnings trends.")

# -----------------------------------------------------------
# Page: Settings (Configurable Settings)
# -----------------------------------------------------------
elif menu == "Settings":
    st.header("Application Settings")
    st.markdown("Adjust the global settings for your ticket management app below.")
    ticket_price = st.number_input("Fixed Ticket Price", min_value=0.0, value=st.session_state.ticket_price, step=0.5)
    st.session_state.ticket_price = ticket_price
    st.success("Settings updated!")
    st.markdown("All new tickets will use the updated ticket price.")

# -----------------------------------------------------------
# Footer
# -----------------------------------------------------------
st.markdown(
    """
    <div class="footer">
        <p>&copy; 2025 Ticket Management App. All rights reserved.</p>
    </div>
    """, unsafe_allow_html=True
)
