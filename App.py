import streamlit as st
import sqlite3
import pandas as pd
import datetime
import plotly.express as px
from io import BytesIO
import requests
import streamlit.components.v1 as components
from streamlit_lottie import st_lottie

# -----------------------------------------------------------
# Initialize Session State Variables
# -----------------------------------------------------------
st.session_state.setdefault("ticket_price", 5.5)
st.session_state.setdefault("dashboard_charts", ["Ticket Count by Status (Bar)",
                                                 "Ticket Status Distribution (Pie)",
                                                 "Tickets Over Time (Line)",
                                                 "Weekly Ticket Trend (Line)"])

# -----------------------------------------------------------
# Page Configuration & Custom CSS (Modern Look & 3D Buttons)
# -----------------------------------------------------------
st.set_page_config(
    page_title="Ticket Management Dashboard",
    page_icon=":ticket:",
    layout="wide"
)

st.markdown(
    """
    <style>
    body {
        background-color: #f5f5f5;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #333;
        margin: 0;
        padding: 0;
    }
    .reportview-container .main .block-container {
        padding: 2rem;
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0 0 15px rgba(0,0,0,0.1);
        max-width: 1200px;
        margin: auto;
    }
    .sidebar .sidebar-content {
        background-color: #ffffff;
    }
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
        margin: 0;
    }
    .header-banner p {
        font-size: 1.5rem;
        margin: 0.5rem 0 0;
    }
    .stMetric {
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0 0 8px rgba(0,0,0,0.1);
    }
    .dataframe th {
        background-color: #f0f0f0;
        color: #333;
    }
    .footer {
        text-align: center;
        font-size: 0.8rem;
        padding: 1rem;
        color: #777;
    }
    /* 3D Button Styling */
    div.stButton > button {
        background-color: #4CAF50;
        color: white;
        font-size: 16px;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        cursor: pointer;
        transition: transform 0.2s, background-color 0.3s ease;
        box-shadow: 0 5px #999;
        margin: 0.5rem;
    }
    div.stButton > button:hover {
        background-color: #45a049;
    }
    div.stButton > button:active {
        background-color: #3e8e41;
        transform: translateY(4px);
        box-shadow: 0 2px #666;
    }
    input, textarea, select {
        font-size: 16px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------------------------------------
# Top Banner (Logo & Tagline)
# -----------------------------------------------------------
st.markdown(
    """
    <div class="header-banner">
        <h1>Ticket Management Dashboard</h1>
        <p>Your Business: Resolve tickets at $5.5 each for consistent earnings</p>
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------------------------------------
# Optional: Lottie Animation for Sidebar
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
# Database Connection (Always Fresh Data)
# -----------------------------------------------------------
def get_db_connection():
    conn = sqlite3.connect("ticket_management.db", check_same_thread=False)
    return conn

conn = get_db_connection()
cursor = conn.cursor()

# -----------------------------------------------------------
# Create Tickets Table
# -----------------------------------------------------------
cursor.execute('''
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    time TEXT,
    batch_name TEXT,
    ticket_number TEXT UNIQUE,
    num_sub_tickets INTEGER DEFAULT 1,
    status TEXT DEFAULT 'Intake',
    pay REAL DEFAULT 5.5,
    comments TEXT DEFAULT '',
    ticket_day TEXT,
    ticket_school TEXT
)
''')
conn.commit()

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
# Sidebar Navigation & Page Routing
# -----------------------------------------------------------
st.sidebar.title("Navigation")
menu = st.sidebar.radio(
    "Go to",
    ["Add Intake Tickets", "Manage Tickets", "Dashboard", "History", "Settings"],
    index=0
)

# ============================================================
# Page: Add Intake Tickets (All new tickets are "Intake")
# ============================================================
def add_intake_tickets():
    st.header("Add Intake Tickets")
    st.markdown(
        """
        **Instructions:**
        - **General Ticket:** Paste or type multiple ticket numbers separated by whitespace.
        - **Large Ticket:** Enter one ticket number and specify the number of sub-tickets.
        """
    )
    raw_batch       = st.text_input("Batch Name", placeholder="Enter batch name (optional)")
    raw_ticket_day  = st.text_input("Ticket Day", placeholder="Enter ticket day (optional)")
    raw_ticket_schl = st.text_input("Ticket School", placeholder="Enter ticket school (optional)")
    
    # Convert inputs to strings safely
    user_batch = str(raw_batch or "").strip()
    ticket_day_val = str(raw_ticket_day or "").strip() or None
    ticket_school_val = str(raw_ticket_schl or "").strip() or None
    
    ticket_entry_type = st.radio("Select Ticket Entry Type", ["General Ticket", "Large Ticket"], index=0)
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    
    if not user_batch:
        cursor.execute("SELECT COUNT(DISTINCT batch_name) FROM tickets")
        batch_count = cursor.fetchone()[0] + 1
        batch_name = f"Batch-{batch_count}"
    else:
        batch_name = user_batch
    
    status_value = "Intake"
    
    if ticket_entry_type == "General Ticket":
        ticket_input = st.text_area("Enter Ticket Numbers", height=150,
                                    help="Separate ticket numbers with whitespace (e.g. 12345 12346 12347)")
        if st.button("Add Tickets"):
            ticket_input = str(ticket_input or "").strip()
            if ticket_input:
                tickets = ticket_input.split()
                success_count = 0
                for tn in tickets:
                    tn = str(tn or "").strip()
                    if tn:
                        try:
                            cursor.execute(
                                """
                                INSERT INTO tickets (date, time, batch_name, ticket_number,
                                num_sub_tickets, status, pay, ticket_day, ticket_school)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    current_date,
                                    current_time,
                                    batch_name,
                                    tn,
                                    1,
                                    status_value,
                                    st.session_state.ticket_price,
                                    ticket_day_val,
                                    ticket_school_val
                                )
                            )
                            success_count += 1
                        except sqlite3.IntegrityError:
                            st.error(f"Ticket '{tn}' already exists.")
                conn.commit()
                if success_count:
                    st.success(f"Successfully added {success_count} Intake tickets.")
                    st.balloons()
            else:
                st.error("Please enter some ticket numbers.")
    else:
        raw_large_ticket = st.text_input("Enter Large Ticket Number", help="This ticket represents a group.")
        large_ticket = str(raw_large_ticket or "").strip()
        sub_ticket_count = st.number_input("Number of Sub-Tickets", min_value=1, value=1, step=1)
        if st.button("Add Large Ticket"):
            if large_ticket:
                try:
                    cursor.execute(
                        """
                        INSERT INTO tickets (date, time, batch_name, ticket_number,
                        num_sub_tickets, status, pay, ticket_day, ticket_school)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            current_date,
                            current_time,
                            batch_name,
                            large_ticket,
                            sub_ticket_count,
                            status_value,
                            st.session_state.ticket_price,
                            ticket_day_val,
                            ticket_school_val
                        )
                    )
                    conn.commit()
                    st.success(f"Successfully added large ticket '{large_ticket}' with {sub_ticket_count} sub-tickets as Intake.")
                    st.balloons()
                except sqlite3.IntegrityError:
                    st.error("Ticket number already exists.")
            else:
                st.error("Please enter a valid ticket number.")

if menu == "Add Intake Tickets":
    add_intake_tickets()

# ============================================================
# Page: Manage Tickets
# ============================================================
def manage_tickets():
    st.header("Manage Tickets")
    
    status_tabs = st.tabs(["Intake Tickets", "Return Tickets", "All Tickets"])
    with status_tabs[0]:
        st.subheader("Intake Tickets")
        df_intake = pd.read_sql("SELECT * FROM tickets WHERE LOWER(status) = 'intake'", conn)
        st.dataframe(df_intake)
    with status_tabs[1]:
        st.subheader("Return Tickets")
        df_return = pd.read_sql("SELECT * FROM tickets WHERE LOWER(status) = 'return'", conn)
        st.dataframe(df_return)
    with status_tabs[2]:
        st.subheader("All Tickets")
        df_all = pd.read_sql("SELECT * FROM tickets", conn)
        st.dataframe(df_all)
    
    with st.expander("Show Filters"):
        col1, col2, col3, col4 = st.columns(4)
        start_date = col1.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
        end_date   = col2.date_input("End Date", datetime.date.today())
        status_filter = col3.selectbox("Status", ["All", "Intake", "Return"])
        type_filter   = col4.selectbox("Ticket Type", ["All", "Intake", "Return"])
        search_term   = st.text_input("Search", help="Search by ticket number or batch name")
        order_by      = st.selectbox("Sort By", ["date", "ticket_number", "status"], index=0)
    
    query = "SELECT * FROM tickets WHERE date BETWEEN ? AND ?"
    params = [start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")]
    if status_filter != "All":
        query += " AND status = ?"
        params.append(status_filter)
    if type_filter != "All":
        query += " AND status = ?"
        params.append(type_filter)
    if search_term:
        query += " AND (ticket_number LIKE ? OR batch_name LIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])
    query += f" ORDER BY {order_by} DESC"
    
    df_filtered = pd.read_sql(query, conn, params=params)
    
    page_size   = st.number_input("Page Size", min_value=5, value=10, step=5)
    page_number = st.number_input("Page Number", min_value=1, value=1, step=1)
    total_tickets = df_filtered.shape[0]
    start_index = (page_number - 1) * page_size
    end_index   = start_index + page_size
    paginated_df = df_filtered.iloc[start_index:end_index]
    
    st.write(f"Showing tickets {start_index+1} to {min(end_index, total_tickets)} of {total_tickets}")
    st.dataframe(paginated_df)
    
    with st.expander("Edit Ticket Details"):
        ticket_to_edit = st.text_input("Enter Ticket Number to Edit", key="edit_ticket")
        if st.button("Load Ticket"):
            ticket_to_edit = str(ticket_to_edit or "").strip()
            if ticket_to_edit:
                cursor.execute("SELECT * FROM tickets WHERE ticket_number=?", (ticket_to_edit,))
                ticket_data = cursor.fetchone()
                if ticket_data:
                    cols = [column[0] for column in cursor.description]
                    ticket_dict = dict(zip(cols, ticket_data))
                    st.write("Current Ticket Details:")
                    st.json(ticket_dict)
                    status_options = ["Intake", "Return"]
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
    
    with st.expander("Delete a Ticket"):
        ticket_to_delete = st.text_input("Ticket Number to Delete", key="delete", help="Exact ticket number required.")
        if st.button("Delete Ticket"):
            ticket_to_delete = str(ticket_to_delete or "").strip()
            if ticket_to_delete:
                cursor.execute("DELETE FROM tickets WHERE ticket_number=?", (ticket_to_delete,))
                conn.commit()
                st.success(f"Ticket '{ticket_to_delete}' deleted.")
            else:
                st.error("Enter a valid ticket number.")
    
    with st.expander("Update Multiple Ticket Statuses"):
        update_ticket_numbers = st.text_input("Enter Ticket Numbers (space-separated)", key="update_status_multi")
        new_status_multi = st.selectbox("New Status", ["Intake", "Return"], key="update_status_select_multi")
        if st.button("Update Status for Multiple Tickets", key="update_status_btn_multi"):
            update_ticket_numbers = str(update_ticket_numbers or "").strip()
            if update_ticket_numbers:
                tickets_list = update_ticket_numbers.split()
                success_count = 0
                for tn in tickets_list:
                    tn = tn.strip()
                    if tn:
                        cursor.execute("UPDATE tickets SET status=? WHERE ticket_number=?", (new_status_multi, tn))
                        success_count += 1
                conn.commit()
                st.success(f"Updated {success_count} tickets to '{new_status_multi}'.")
            else:
                st.error("Please enter at least one ticket number.")
    
    with st.expander("Update All Filtered Tickets to Return"):
        if st.button("Update All Filtered Tickets to Return"):
            if not df_filtered.empty:
                ticket_numbers = df_filtered["ticket_number"].tolist()
                count = 0
                for tn in ticket_numbers:
                    cursor.execute("UPDATE tickets SET status='Return' WHERE ticket_number=?", (tn,))
                    count += 1
                conn.commit()
                st.success(f"Updated {count} tickets to 'Return'.")
            else:
                st.error("No tickets found in current filter.")
    
    st.markdown("### Copy Tickets Data")
    if st.button("Copy Filtered Tickets to Clipboard"):
        copy_text = df_filtered.to_csv(index=False)
        html_code = f"""
        <textarea id="copyText" style="opacity:0;">{copy_text}</textarea>
        <script>
        function copyToClipboard() {{
          var copyText = document.getElementById("copyText");
          copyText.select();
          copyText.setSelectionRange(0, 99999);
          document.execCommand("copy");
        }}
        copyToClipboard();
        </script>
        """
        components.html(html_code, height=0)
        st.success("Filtered tickets copied to clipboard!")
    
    if st.button("Copy All Tickets to Clipboard"):
        copy_text_all = pd.read_sql("SELECT * FROM tickets", conn).to_csv(index=False)
        html_code_all = f"""
        <textarea id="copyTextAll" style="opacity:0;">{copy_text_all}</textarea>
        <script>
        function copyToClipboardAll() {{
          var copyText = document.getElementById("copyTextAll");
          copyText.select();
          copyText.setSelectionRange(0, 99999);
          document.execCommand("copy");
        }}
        copyToClipboardAll();
        </script>
        """
        components.html(html_code_all, height=0)
        st.success("All tickets copied to clipboard!")
    
    with st.expander("Execute Custom SQL Query"):
        sql_query = st.text_area("Enter SQL Query")
        if st.button("Execute Query"):
            try:
                cursor.execute(sql_query)
                if sql_query.strip().lower().startswith("select"):
                    result = cursor.fetchall()
                    cols = [col[0] for col in cursor.description]
                    df_result = pd.DataFrame(result, columns=cols)
                    st.dataframe(df_result)
                else:
                    conn.commit()
                    st.success("Query executed successfully.")
            except Exception as e:
                st.error(f"Error executing query: {e}")

if menu == "Manage Tickets":
    manage_tickets()

# -----------------------------------------------------------
# Page: Dashboard
# -----------------------------------------------------------
def dashboard():
    st.header("Dashboard Analytics")
    df = pd.read_sql("SELECT * FROM tickets", conn)
    
    all_batches = ["All"] + sorted(set(df["batch_name"].dropna().tolist()))
    selected_batch = st.selectbox("Select Batch to View", all_batches)
    if selected_batch != "All":
        df = df[df["batch_name"] == selected_batch]
    
    if "pay" not in df.columns:
        df["pay"] = st.session_state.ticket_price
    if "num_sub_tickets" not in df.columns:
        df["num_sub_tickets"] = 1

    # Calculate earnings
    estimated_earning = (df[df["status"]=="Intake"]["pay"] * df[df["status"]=="Intake"]["num_sub_tickets"]).sum()
    actual_earning = (df[df["status"]=="Return"]["pay"] * df[df["status"]=="Return"]["num_sub_tickets"]).sum()
    total_estimated = estimated_earning + actual_earning  # combined earnings
    
    st.metric("Total Estimated Earnings Till Now", f"${total_estimated:.2f}")
    st.metric("Estimated Earnings (Open)", f"${estimated_earning:.2f}")
    st.metric("Actual Earnings (Returned)", f"${actual_earning:.2f}")
    
    # Interactive Earnings Over Time Chart
    try:
        df["date"] = pd.to_datetime(df["date"])
        earnings_over_time = df.groupby("date").apply(lambda x: (x["pay"] * x["num_sub_tickets"]).sum()).reset_index(name="earnings")
        fig = px.line(earnings_over_time, x="date", y="earnings", title="Earnings Over Time", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error generating earnings chart: {e}")
    
    # 3D Buttons to reveal ticket lists
    colA, colB = st.columns([1, 1])
    with colA:
        if st.button("Show Return Tickets"):
            with st.expander("List of Returned Tickets"):
                st.dataframe(df[df["status"]=="Return"])
    with colB:
        if st.button("Show Intake Tickets"):
            with st.expander("List of Intake Tickets"):
                st.dataframe(df[df["status"]=="Intake"])
    
    st.markdown("### Ticket Data Overview")
    st.dataframe(df.style.format({"pay": "${:,.2f}"}))
    
    chart_type = st.selectbox("Select Chart Type", 
                              ["Ticket Count by Status (Bar)",
                               "Ticket Status Distribution (Pie)",
                               "Tickets Over Time (Line)",
                               "Weekly Ticket Trend (Line)"])
    
    if chart_type == "Ticket Count by Status (Bar)":
        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        fig = px.bar(status_counts, x="status", y="count", color="status", title="Ticket Count by Status", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    elif chart_type == "Ticket Status Distribution (Pie)":
        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        fig = px.pie(status_counts, names="status", values="count", title="Ticket Status Distribution", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    elif chart_type == "Tickets Over Time (Line)":
        try:
            tickets_over_time = df.groupby("date").size().reset_index(name="count")
            fig = px.line(tickets_over_time, x="date", y="count", title="Tickets Over Time", template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error generating time series chart: {e}")
    elif chart_type == "Weekly Ticket Trend (Line)":
        try:
            weekly = df.groupby(pd.Grouper(key="date", freq="W")).size().reset_index(name="tickets")
            fig = px.line(weekly, x="date", y="tickets", title="Weekly Ticket Trend", template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error generating weekly trend chart: {e}")
    
    st.markdown("### Business Insights")
    total_tickets = df["num_sub_tickets"].sum()
    return_count = df[df["status"]=="Return"]["num_sub_tickets"].sum()
    completion_rate = (return_count / total_tickets * 100) if total_tickets else 0
    st.markdown(f"**Overall Ticket Completion Rate:** {completion_rate:.1f}%")
    
    if not df.empty:
        top_batch = df['batch_name'].value_counts().idxmax()
    else:
        top_batch = "N/A"
    st.markdown(f"**Top Performing Batch:** {top_batch}")
    
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Tickets as CSV", data=csv, file_name="tickets.csv", mime="text/csv")
    
    towrite = BytesIO()
    df.to_excel(towrite, index=False, sheet_name="Tickets")
    towrite.seek(0)
    st.download_button("Download Tickets as Excel", data=towrite, file_name="tickets.xlsx", mime="application/vnd.ms-excel")
    
    st.info("Review these interactive charts and insights for a complete view of your ticket operations and earnings trends.")

if menu == "Dashboard":
    dashboard()

# ============================================================
# Page: History (Earnings and Batch Details)
# ============================================================
def history_page():
    st.header("Earnings History")
    st.markdown("Below is the history of earnings and ticket counts grouped by batch.")
    
    df_history = pd.read_sql("SELECT batch_name, COUNT(*) as ticket_count, SUM(pay * num_sub_tickets) as earnings FROM tickets GROUP BY batch_name ORDER BY batch_name", conn)
    st.dataframe(df_history)
    
    fig_history = px.bar(df_history, x="batch_name", y="earnings", title="Earnings by Batch", template="plotly_white")
    st.plotly_chart(fig_history, use_container_width=True)
    
    fig_count = px.bar(df_history, x="batch_name", y="ticket_count", title="Ticket Count by Batch", template="plotly_white")
    st.plotly_chart(fig_count, use_container_width=True)
    
    st.markdown("### Batch Details")
    batches = df_history["batch_name"].tolist()
    for batch in batches:
        with st.expander(f"View Tickets for {batch}"):
            df_batch = pd.read_sql("SELECT * FROM tickets WHERE batch_name = ?", conn, params=(batch,))
            st.dataframe(df_batch)

if menu == "History":
    history_page()

# ============================================================
# Page: Settings
# ============================================================
def settings_page():
    st.header("Application Settings")
    st.markdown("Adjust the global settings for your ticket management app below.")
    
    ticket_price = st.number_input("Fixed Ticket Price", min_value=0.0, value=st.session_state.ticket_price, step=0.5)
    st.session_state.ticket_price = ticket_price
    
    dashboard_options = st.multiselect("Select Dashboard Charts to Display", 
                                       options=["Ticket Count by Status (Bar)",
                                                "Ticket Status Distribution (Pie)",
                                                "Tickets Over Time (Line)",
                                                "Weekly Ticket Trend (Line)"],
                                       default=st.session_state.dashboard_charts)
    st.session_state.dashboard_charts = dashboard_options
    
    st.success("Settings updated!")
    st.markdown("All new tickets will use the updated ticket price. Dashboard charts will display as configured.")

if menu == "Settings":
    settings_page()

# ============================================================
# Footer
# ============================================================
st.markdown(
    """
    <div class="footer">
        <p>&copy; 2025 Ticket Management App. All rights reserved.</p>
    </div>
    """,
    unsafe_allow_html=True
)