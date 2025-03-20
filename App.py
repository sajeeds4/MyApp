import streamlit as st
import sqlite3
import pandas as pd
import datetime
import numpy as np
import plotly.express as px
from io import BytesIO
import requests
import streamlit.components.v1 as components
from streamlit_lottie import st_lottie

# ----------------------------
# Session State Initialization
# ----------------------------
st.session_state.setdefault("ticket_price", 5.5)
st.session_state.setdefault("dashboard_charts", ["Ticket Count by Status (Bar)"])

# ----------------------------
# Page Configuration & Custom CSS
# ----------------------------
st.set_page_config(
    page_title="Ticket Management Dashboard",
    page_icon=":ticket:",
    layout="wide"
)

st.markdown(
    """
    <style>
    /* Global styling */
    body {
        background-color: #f5f5f5;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #333;
        margin: 0;
        padding: 0;
    }
    .reportview-container .main .block-container {
        padding: 2rem;
        background-color: #fff;
        border-radius: 10px;
        box-shadow: 0 0 15px rgba(0,0,0,0.1);
        max-width: 1200px;
        margin: auto;
    }
    .sidebar .sidebar-content {
        background-color: #fff;
    }
    /* Header Banner */
    .header-banner {
        background-image: url('https://via.placeholder.com/1500x200.png?text=Your+Business+Tagline');
        background-size: cover;
        background-position: center;
        border-radius: 10px;
        margin-bottom: 1rem;
        padding: 2rem;
        text-align: center;
        color: #fff;
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
    /* Metric Cards */
    .stMetric {
        background-color: #fff;
        border-radius: 10px;
        box-shadow: 0 0 8px rgba(0,0,0,0.1);
    }
    /* DataFrame Styling */
    .dataframe th {
        background-color: #f0f0f0;
        color: #333;
    }
    /* Footer Styling */
    .footer {
        text-align: center;
        font-size: 0.8rem;
        padding: 1rem;
        color: #777;
    }
    /* 3D Button Styling */
    div.stButton > button {
        background-color: #4CAF50;
        color: #fff;
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
    /* Responsive CSS */
    @media (max-width: 768px) {
        .reportview-container .main .block-container { padding: 1rem; max-width: 100%; }
        .header-banner h1 { font-size: 2rem; }
        .header-banner p { font-size: 1.2rem; }
        div.stButton > button { padding: 8px 16px; font-size: 14px; }
    }
    /* Custom Sidebar Menu */
    .custom-menu a {
        display: block;
        text-decoration: none;
        padding: 10px;
        margin-bottom: 5px;
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        text-align: center;
    }
    .custom-menu a:hover {
        background-color: #45a049;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ----------------------------
# Top Banner
# ----------------------------
st.markdown(
    """
    <div class="header-banner">
        <h1>Ticket Management Dashboard</h1>
        <p>Your Business: Repair laptops and earn $5.5 per ticket</p>
    </div>
    """,
    unsafe_allow_html=True
)

# ----------------------------
# Optional: Lottie Animation for Sidebar
# ----------------------------
def load_lottie(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_animation = load_lottie("https://assets9.lottiefiles.com/packages/lf20_mjlh3hcy.json")
if lottie_animation:
    st.sidebar.markdown("<h4 style='text-align:center;'>Welcome!</h4>", unsafe_allow_html=True)
    st_lottie(lottie_animation, height=150, key="lottie")

# ----------------------------
# Database Connection & Table Creation
# ----------------------------
def get_db_connection():
    conn = sqlite3.connect("ticket_management.db", check_same_thread=False)
    return conn

conn = get_db_connection()
cursor = conn.cursor()

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
cols_info = cursor.fetchall()
cols_names = [col[1] for col in cols_info]
if "ticket_day" not in cols_names:
    cursor.execute("ALTER TABLE tickets ADD COLUMN ticket_day TEXT")
    conn.commit()
if "ticket_school" not in cols_names:
    cursor.execute("ALTER TABLE tickets ADD COLUMN ticket_school TEXT")
    conn.commit()

# ----------------------------
# Custom Sidebar Navigation Menu using HTML Links
# ----------------------------
# Use query parameters to drive navigation.
params = st.experimental_get_query_params()
current_page = params.get("page", ["add"])[0]

st.sidebar.markdown('<div class="custom-menu">'
                    '<a href="?page=add">Add Tickets</a>'
                    '<a href="?page=manage">Manage Tickets</a>'
                    '<a href="?page=dashboard">Dashboard</a>'
                    '<a href="?page=income">Income</a>'
                    '<a href="?page=history">History</a>'
                    '<a href="?page=settings">Settings</a>'
                    '</div>', unsafe_allow_html=True)

# ----------------------------
# Page Functions
# ----------------------------

# Page: Add Tickets (All new tickets are "Intake")
def add_tickets_page():
    st.header("Add Tickets")
    st.markdown("Work with laptop repair tickets. For each ticket, you earn $5.5. For large tickets (e.g. a batch of 12 devices), the system will count it as multiple devices.")
    
    raw_batch       = st.text_input("Batch Name", placeholder="Enter batch name (optional)")
    raw_ticket_day  = st.text_input("Ticket Day", placeholder="Enter ticket day (optional)")
    raw_ticket_schl = st.text_input("Ticket School", placeholder="Enter ticket school (optional)")
    
    user_batch = str(raw_batch or "").strip()
    ticket_day_val = str(raw_ticket_day or "").strip() or None
    ticket_school_val = str(raw_ticket_schl or "").strip() or None
    
    ticket_type = st.radio("Ticket Type", ["Single Ticket", "Large Ticket"], index=0)
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    
    if not user_batch:
        cursor.execute("SELECT COUNT(DISTINCT batch_name) FROM tickets")
        batch_count = cursor.fetchone()[0] + 1
        batch_name = f"Batch-{batch_count}"
    else:
        batch_name = user_batch
    
    status_value = "Intake"
    
    if ticket_type == "Single Ticket":
        ticket_input = st.text_area("Enter Ticket Numbers", height=150,
                                    help="Enter one or more ticket numbers separated by spaces (each representing one laptop)")
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
                                (current_date, current_time, batch_name, tn, 1, status_value,
                                 st.session_state.ticket_price, ticket_day_val, ticket_school_val)
                            )
                            success_count += 1
                        except sqlite3.IntegrityError:
                            st.error(f"Ticket '{tn}' already exists.")
                conn.commit()
                if success_count:
                    st.success(f"Successfully added {success_count} tickets to batch {batch_name}.")
                    st.balloons()
            else:
                st.error("Please enter ticket numbers.")
    else:
        raw_large_ticket = st.text_input("Enter Large Ticket Number", help="This represents a batch of devices (e.g. 12 devices)")
        large_ticket = str(raw_large_ticket or "").strip()
        # For large tickets, assume each counts as 12 devices.
        sub_ticket_count = st.number_input("Number of Devices in Ticket", min_value=1, value=12, step=1)
        if st.button("Add Large Ticket"):
            if large_ticket:
                try:
                    cursor.execute(
                        """
                        INSERT INTO tickets (date, time, batch_name, ticket_number,
                        num_sub_tickets, status, pay, ticket_day, ticket_school)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (current_date, current_time, batch_name, large_ticket, sub_ticket_count, status_value,
                         st.session_state.ticket_price, ticket_day_val, ticket_school_val)
                    )
                    conn.commit()
                    st.success(f"Successfully added large ticket '{large_ticket}' with {sub_ticket_count} devices to batch {batch_name}.")
                    st.balloons()
                except sqlite3.IntegrityError:
                    st.error("Ticket number already exists.")
            else:
                st.error("Please enter a valid ticket number.")

# Page: Manage Tickets
def manage_tickets_page():
    st.header("Manage Tickets")
    
    tabs = st.tabs(["Intake Tickets", "Return Tickets", "All Tickets"])
    with tabs[0]:
        st.subheader("Intake Tickets")
        df_intake = pd.read_sql("SELECT * FROM tickets WHERE LOWER(status) = 'intake'", conn)
        st.dataframe(df_intake)
    with tabs[1]:
        st.subheader("Return Tickets")
        df_return = pd.read_sql("SELECT * FROM tickets WHERE LOWER(status) = 'return'", conn)
        st.dataframe(df_return)
    with tabs[2]:
        st.subheader("All Tickets")
        df_all = pd.read_sql("SELECT * FROM tickets", conn)
        st.dataframe(df_all)
    
    with st.expander("Show Filters"):
        c1, c2, c3, c4 = st.columns(4)
        start_date = c1.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
        end_date = c2.date_input("End Date", datetime.date.today())
        status_filter = c3.selectbox("Status", ["All", "Intake", "Return"])
        search_term = c4.text_input("Search", help="Search by ticket number or batch name")
        order_by = st.selectbox("Sort By", ["date", "ticket_number", "status"], index=0)
    
    query = "SELECT * FROM tickets WHERE date BETWEEN ? AND ?"
    params = [start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")]
    if status_filter != "All":
        query += " AND status = ?"
        params.append(status_filter)
    if search_term:
        query += " AND (ticket_number LIKE ? OR batch_name LIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])
    query += f" ORDER BY {order_by} DESC"
    
    df_filtered = pd.read_sql(query, conn, params=params)
    
    page_size = st.number_input("Page Size", min_value=5, value=10, step=5)
    page_number = st.number_input("Page Number", min_value=1, value=1, step=1)
    total_tickets = df_filtered.shape[0]
    start_index = (page_number - 1) * page_size
    end_index = start_index + page_size
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
                    cols = [col[0] for col in cursor.description]
                    ticket_dict = dict(zip(cols, ticket_data))
                    st.write("Current Ticket Details:")
                    st.json(ticket_dict)
                    new_status = st.selectbox("Update Status", ["Intake", "Return"], index=0)
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
    manage_tickets_page()

# ============================================================
# Page: Dashboard (Simple Sine Wave Graph as Daily Income Trend)
# ============================================================
def dashboard_page():
    st.header("Dashboard")
    
    # Generate a sine wave as a placeholder for daily income trend
    x = np.linspace(0, 4 * np.pi, 100)
    y = np.sin(x) * 100  # scale the sine wave to represent earnings
    df_sine = pd.DataFrame({"Time": x, "Earnings": y})
    
    st.markdown("### Daily Income Trend (Sine Wave Simulation)")
    fig_sine = px.line(df_sine, x="Time", y="Earnings", title="Daily Income Trend", template="plotly_white")
    st.plotly_chart(fig_sine, use_container_width=True)
    
    # Display simplified earnings metrics based on database
    df = pd.read_sql("SELECT * FROM tickets", conn)
    if "pay" not in df.columns:
        df["pay"] = st.session_state.ticket_price
    if "num_sub_tickets" not in df.columns:
        df["num_sub_tickets"] = 1
    
    estimated_earning = (df[df["status"]=="Intake"]["pay"] * df[df["status"]=="Intake"]["num_sub_tickets"]).sum()
    actual_earning = (df[df["status"]=="Return"]["pay"] * df[df["status"]=="Return"]["num_sub_tickets"]).sum()
    total_earnings = estimated_earning + actual_earning
    
    st.metric("Total Estimated Earnings Till Now", f"${total_earnings:.2f}")
    st.metric("Estimated Earnings (Open)", f"${estimated_earning:.2f}")
    st.metric("Actual Earnings (Returned)", f"${actual_earning:.2f}")

if menu == "Dashboard":
    dashboard_page()

# ============================================================
# Page: Income (Detailed Income Information)
# ============================================================
def income_page():
    st.header("Income Overview")
    st.markdown("This section shows how much you've earned so far and the estimated value of tickets still open.")
    
    df = pd.read_sql("SELECT * FROM tickets", conn)
    if "pay" not in df.columns:
        df["pay"] = st.session_state.ticket_price
    if "num_sub_tickets" not in df.columns:
        df["num_sub_tickets"] = 1
    
    # Calculate earnings from returned tickets (actual) and from open (intake) tickets (estimated)
    actual_income = (df[df["status"]=="Return"]["pay"] * df[df["status"]=="Return"]["num_sub_tickets"]).sum()
    estimated_income = (df[df["status"]=="Intake"]["pay"] * df[df["status"]=="Intake"]["num_sub_tickets"]).sum()
    total_income = actual_income + estimated_income
    
    st.metric("Total Income (Combined)", f"${total_income:.2f}")
    st.metric("Actual Income (Returned)", f"${actual_income:.2f}")
    st.metric("Potential Income (Open)", f"${estimated_income:.2f}")
    
    # Daily income trend (aggregated by date from returned tickets)
    try:
        df["date"] = pd.to_datetime(df["date"])
        df_return = df[df["status"]=="Return"]
        daily_income = df_return.groupby("date").apply(lambda x: (x["pay"] * x["num_sub_tickets"]).sum()).reset_index(name="Income")
        fig_income = px.line(daily_income, x="date", y="Income", title="Daily Income Trend", template="plotly_white")
        st.plotly_chart(fig_income, use_container_width=True)
    except Exception as e:
        st.error(f"Error generating daily income trend: {e}")

if menu == "Income":
    income_page()

# ============================================================
# Page: History (Earnings and Batch Details with Return by Batch)
# ============================================================
def history_page():
    st.header("History")
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
            colX, colY = st.columns([1, 1])
            with colX:
                if st.button(f"Return all tickets for {batch}", key=f"return_{batch}"):
                    cursor.execute("UPDATE tickets SET status='Return' WHERE batch_name=?", (batch,))
                    conn.commit()
                    st.success(f"All tickets in batch {batch} marked as Return.")
            with colY:
                df_batch = pd.read_sql("SELECT * FROM tickets WHERE batch_name = ?", conn, params=(batch,))
                st.dataframe(df_batch)

if menu == "History":
    history_page()

# ============================================================
# Page: Settings
# ============================================================
def settings_page():
    st.header("Settings")
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
    st.markdown("All new tickets will use the updated ticket price.")

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