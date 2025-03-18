import streamlit as st
import sqlite3
import pandas as pd
import datetime
import plotly.express as px
from io import BytesIO
import requests
from streamlit_lottie import st_lottie

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
        padding: 2rem;
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
    /* KPI card styling */
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
# Load Lottie Animation for Navigation
# -----------------------------------------------------------
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_nav = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_mjlh3hcy.json")
if lottie_nav:
    st.sidebar.markdown("<h4 style='text-align: center;'>Navigation Animation</h4>", unsafe_allow_html=True)
    st_lottie(lottie_nav, height=150, key="nav")

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
# Create Tickets Table with additional columns: comments, ticket_day, ticket_school
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
    comments TEXT DEFAULT '',
    ticket_day TEXT,
    ticket_school TEXT
)
''')
conn.commit()

# Ensure schema compatibility for new optional columns
cursor.execute("PRAGMA table_info(tickets)")
columns_info = cursor.fetchall()
column_names = [col[1] for col in columns_info]
if "ticket_day" not in column_names:
    cursor.execute("ALTER TABLE tickets ADD COLUMN ticket_day TEXT")
    conn.commit()
if "ticket_school" not in column_names:
    cursor.execute("ALTER TABLE tickets ADD COLUMN ticket_school TEXT")
    conn.commit()

# -----------------------------------------------------------
# Sidebar Navigation (with interactive animations)
# -----------------------------------------------------------
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to", 
                        ["Add Intake Tickets", "Add Return Tickets", "Manage Tickets", "Dashboard", "Settings"],
                        index=0)

# -----------------------------------------------------------
# Function: Add Tickets (for Intake or Return)
# -----------------------------------------------------------
def add_tickets(ticket_category):
    with st.spinner("Loading Add Tickets page..."):
        st.header(f"Add {ticket_category} Tickets")
        st.markdown(
            """
            **Instructions:**
            - **General Ticket:** Paste or type multiple ticket numbers separated by whitespace.
            - **Large Ticket:** Enter one ticket number and specify the number of sub-tickets.
            """
        )
        # Optional user-provided inputs for Batch Name, Ticket Day, Ticket School
        user_batch = st.text_input("Batch Name", placeholder="Enter batch name (optional)")
        ticket_day = st.text_input("Ticket Day", placeholder="Enter ticket day (optional)")
        ticket_school = st.text_input("Ticket School", placeholder="Enter ticket school (optional)")
        
        ticket_entry_type = st.radio("Select Ticket Entry Type", 
                                     ["General Ticket", "Large Ticket"],
                                     index=0,
                                     help="Choose how to add your tickets.")
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        
        # If batch name not provided, auto-generate one
        if user_batch.strip() == "":
            cursor.execute("SELECT COUNT(DISTINCT batch_name) FROM tickets")
            batch_count = cursor.fetchone()[0] + 1
            batch_name = f"Batch-{batch_count}"
        else:
            batch_name = user_batch.strip()
        
        # Determine the default status based on ticket category
        if ticket_category == "Intake":
            status_value = "Intake"
        else:
            status_value = "Returned"
        
        if ticket_entry_type == "General Ticket":
            ticket_input = st.text_area("Enter Ticket Numbers", 
                                        height=150, 
                                        help="Separate ticket numbers with whitespace. Ex: 12345 12346 12347")
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
                                    """INSERT INTO tickets 
                                    (date, time, batch_name, ticket_number, num_sub_tickets, status, type, pay, ticket_day, ticket_school)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                    (current_date, current_time, batch_name, tn, 1, status_value, ticket_category, st.session_state.ticket_price, 
                                     ticket_day.strip() if ticket_day.strip() != "" else None, 
                                     ticket_school.strip() if ticket_school.strip() != "" else None)
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
                            """INSERT INTO tickets 
                            (date, time, batch_name, ticket_number, num_sub_tickets, status, type, pay, ticket_day, ticket_school)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (current_date, current_time, batch_name, large_ticket, sub_ticket_count, status_value, ticket_category, st.session_state.ticket_price,
                             ticket_day.strip() if ticket_day.strip() != "" else None,
                             ticket_school.strip() if ticket_school.strip() != "" else None)
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
    with st.spinner("Loading Manage Tickets page..."):
        st.header("Manage Tickets")
        
        # -----------------------------------------------------------
        # New: Header Tabs for Different Statuses
        # -----------------------------------------------------------
        status_tabs = st.tabs(["Intake", "Done", "Returned", "All"])
        with status_tabs[0]:
            st.subheader("Intake Tickets")
            df_intake = pd.read_sql("SELECT * FROM tickets WHERE status = 'Intake'", conn)
            st.dataframe(df_intake)
        with status_tabs[1]:
            st.subheader("Done Tickets")
            df_done = pd.read_sql("SELECT * FROM tickets WHERE status = 'Done'", conn)
            st.dataframe(df_done)
        with status_tabs[2]:
            st.subheader("Returned Tickets")
            df_returned = pd.read_sql("SELECT * FROM tickets WHERE status = 'Returned'", conn)
            st.dataframe(df_returned)
        with status_tabs[3]:
            st.subheader("All Tickets")
            df_all = pd.read_sql("SELECT * FROM tickets", conn)
            st.dataframe(df_all)
        
        st.markdown("Use the filters below to locate and manage your tickets:")
        
        col1, col2, col3, col4 = st.columns(4)
        start_date = col1.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
        end_date = col2.date_input("End Date", datetime.date.today())
        status_filter = col3.selectbox("Status", ["All", "Intake", "Done", "Returned"])
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
                        
                        # Allow updating status with new options: Intake, Done, Returned
                        status_options = ["Intake", "Done", "Returned"]
                        try:
                            default_index = status_options.index(ticket_dict["status"])
                        except ValueError:
                            default_index = 0
                        new_status = st.selectbox("Update Status", status_options, index=default_index)
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
        
        with st.expander("Resolve a Ticket"):
            ticket_to_resolve = st.text_input("Ticket Number to Resolve", key="resolve", help="Enter the exact ticket number.")
            if st.button("Resolve Ticket"):
                ticket_to_resolve = ticket_to_resolve.strip()
                if ticket_to_resolve:
                    cursor.execute("UPDATE tickets SET status='Done' WHERE ticket_number=?", (ticket_to_resolve,))
                    conn.commit()
                    st.success(f"Ticket '{ticket_to_resolve}' marked as Done.")
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
        
        # -----------------------------------------------------------
        # New: Separate Box for Updating Multiple Ticket Statuses
        # -----------------------------------------------------------
        with st.expander("Update Multiple Ticket Statuses"):
            update_ticket_numbers = st.text_input("Enter Ticket Numbers to Update (separated by space)", key="update_status_multi")
            new_status_multi = st.selectbox("New Status", ["Intake", "Done", "Returned"], key="update_status_select_multi")
            if st.button("Update Status for Multiple Tickets", key="update_status_btn_multi"):
                update_ticket_numbers = update_ticket_numbers.strip()
                if update_ticket_numbers:
                    tickets_list = update_ticket_numbers.split()
                    success_count = 0
                    for tn in tickets_list:
                        tn = tn.strip()
                        if tn:
                            cursor.execute("UPDATE tickets SET status=? WHERE ticket_number=?", (new_status_multi, tn))
                            success_count += 1
                    conn.commit()
                    st.success(f"Updated status for {success_count} tickets to '{new_status_multi}'.")
                else:
                    st.error("Please enter at least one ticket number.")
        
        st.info("Use the above filters and actions to efficiently manage your tickets.")

# -----------------------------------------------------------
# Page: Dashboard (Fully Graphical, Interactive Analytics & Business Insights)
# -----------------------------------------------------------
elif menu == "Dashboard":
    with st.spinner("Loading Dashboard..."):
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
        unresolved_tickets = df[df["status"].isin(["Intake", "Done"])].shape[0]
        resolved_tickets = df[df["status"] == "Returned"].shape[0]
        
        # Display KPI Cards
        kpi_cols = st.columns(5)
        kpi_cols[0].metric("Total Tickets", total_tickets)
        kpi_cols[1].metric("Returned Tickets", resolved_tickets)
        kpi_cols[2].metric("In-Progress (Intake/Done)", unresolved_tickets)
        kpi_cols[3].metric("Estimated Earnings (Intake)", f"${estimated_earning:.2f}")
        kpi_cols[4].metric("Actual Earnings (Return)", f"${actual_earning:.2f}")
        
        st.markdown("### Ticket Data Overview")
        st.dataframe(df.style.format({"pay": "${:,.2f}"}))
        
        # Dropdown to select chart type
        chart_type = st.selectbox("Select Chart Type", 
                                  ["Ticket Count by Status (Bar)", "Ticket Count by Category (Bar)",
                                   "Ticket Status Distribution (Pie)", "Tickets Over Time (Line)", "Weekly Ticket Trend (Line)"])
        
        if chart_type == "Ticket Count by Status (Bar)":
            status_counts = df["status"].value_counts().reset_index()
            status_counts.columns = ["status", "count"]
            fig = px.bar(status_counts, x="status", y="count", color="status", title="Ticket Count by Status",
                         template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
        elif chart_type == "Ticket Count by Category (Bar)":
            type_counts = df["type"].value_counts().reset_index()
            type_counts.columns = ["type", "count"]
            fig = px.bar(type_counts, x="type", y="count", color="type", title="Ticket Count by Category",
                         template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
        elif chart_type == "Ticket Status Distribution (Pie)":
            status_counts = df["status"].value_counts().reset_index()
            status_counts.columns = ["status", "count"]
            fig = px.pie(status_counts, names="status", values="count", title="Ticket Status Distribution",
                         template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
        elif chart_type == "Tickets Over Time (Line)":
            try:
                df["date"] = pd.to_datetime(df["date"])
                tickets_over_time = df.groupby("date").size().reset_index(name="count")
                fig = px.line(tickets_over_time, x="date", y="count", title="Tickets Over Time",
                              template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error("Error generating time series chart: " + str(e))
        elif chart_type == "Weekly Ticket Trend (Line)":
            try:
                df["date"] = pd.to_datetime(df["date"])
                weekly = df.groupby(pd.Grouper(key="date", freq="W")).size().reset_index(name="tickets")
                fig = px.line(weekly, x="date", y="tickets", title="Weekly Ticket Trend", template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error("Error generating weekly trend chart: " + str(e))
        
        # Business Insights Section
        st.markdown("### Business Insights")
        completion_rate = (resolved_tickets / total_tickets * 100) if total_tickets else 0
        st.markdown(f"**Overall Ticket Completion Rate:** {completion_rate:.1f}%")
        top_batch = df['batch_name'].value_counts().idxmax() if total_tickets > 0 else "N/A"
        st.markdown(f"**Top Performing Batch:** {top_batch}")
        
        # Export Options
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Tickets as CSV", data=csv, file_name="tickets.csv", mime="text/csv")
        
        towrite = BytesIO()
        df.to_excel(towrite, index=False, sheet_name="Tickets")
        towrite.seek(0)
        st.download_button("Download Tickets as Excel", data=towrite, file_name="tickets.xlsx", mime="application/vnd.ms-excel")
        
        st.info("Review these interactive charts and insights for a complete view of your ticket operations and earnings trends.")

# -----------------------------------------------------------
# Page: Settings (Configurable Settings)
# -----------------------------------------------------------
elif menu == "Settings":
    with st.spinner("Loading Settings..."):
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
