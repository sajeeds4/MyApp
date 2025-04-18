import streamlit as st
import sqlite3
import pandas as pd
import datetime
import requests
from streamlit_lottie import st_lottie
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import numpy as np
import streamlit.components.v1 as components

# -----------------------------------------------------------
# Configuration
# -----------------------------------------------------------
st.set_page_config(
    page_title="Ticket Management System",
    page_icon="🎟️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------
# Global Status Definitions (Customize as you wish)
# -----------------------------------------------------------
# These are the possible statuses stored in the DB.
AVAILABLE_STATUSES = [
    "Intake",
    "Return",        # previously "Ready to Deliver" in DB
    "Delivered",
    "On Hold",       # Example of a custom status
    "Cancelled"      # Another custom status
]

# Map DB statuses to their display labels in the UI
STATUS_LABELS = {
    "Intake": "Intake",
    "Return": "Ready to Deliver",
    "Delivered": "Delivered",
    "On Hold": "On Hold",
    "Cancelled": "Cancelled"
}

def display_status(status_in_db: str) -> str:
    """Convert a DB status into a user-facing label."""
    return STATUS_LABELS.get(status_in_db, status_in_db)

def get_db_status_from_display(ui_label: str) -> str:
    """Given the user-facing label, return the DB status key."""
    for db_val, label in STATUS_LABELS.items():
        if label == ui_label:
            return db_val
    # Fallback: if not found in dictionary
    return ui_label

# -----------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------
if "ticket_price" not in st.session_state:
    st.session_state.ticket_price = 5.5
if "company_name" not in st.session_state:
    st.session_state.company_name = "My Business"
if "batch_prefix" not in st.session_state:
    st.session_state.batch_prefix = "Batch-"
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "active_page" not in st.session_state:
    st.session_state.active_page = "Dashboard"  # default page

# -----------------------------------------------------------
# Styling (Basic CSS to hide branding and set background)
# -----------------------------------------------------------
def load_css():
    if st.session_state.dark_mode:
        primary_color = "#1E88E5"
        bg_color = "#121212"
        text_color = "#E0E0E0"
    else:
        primary_color = "#4CAF50"
        bg_color = "#f8f9fa"
        text_color = "#333333"
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {bg_color};
            color: {text_color};
        }}
        /* Hide Streamlit Branding */
        #MainMenu, footer, header {{
            visibility: hidden;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

load_css()

# -----------------------------------------------------------
# Lottie Animations
# -----------------------------------------------------------
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

animations = {
    "tickets": load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_mjlh3hcy.json"),
    "dashboard": load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_qp1q7mct.json"),
    "success": load_lottieurl("https://assets6.lottiefiles.com/packages/lf20_vi8cufn8.json"),
    "money": load_lottieurl("https://assets7.lottiefiles.com/packages/lf20_SzPMKj.json"),
    "settings": load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_ukrsqhcj.json")
}

# -----------------------------------------------------------
# Database Setup
# -----------------------------------------------------------
def get_db_connection():
    conn = sqlite3.connect("ticket_management.db", check_same_thread=False)
    return conn

def setup_database():
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
        -- "Return" means the ticket is "Ready to Deliver"
        status TEXT DEFAULT 'Intake',
        pay REAL DEFAULT 5.5,
        comments TEXT DEFAULT '',
        ticket_day TEXT,
        ticket_school TEXT
    )
    ''')
    conn.commit()
    return conn

conn = setup_database()
cursor = conn.cursor()

# -----------------------------------------------------------
# Navigation (Add new pages to navigation)
# -----------------------------------------------------------
def render_navbar():
    pages = {
        "Dashboard": "📊",
        "Add Tickets": "➕",
        "View Tickets": "👁️",
        "Manage Tickets": "🔄",
        "Bulk Ticket Comparison": "🔍",
        "SQL Query Converter": "📝",
        "Income": "💰",
        "Batches": "🗂️",
        "AI Analysis": "🤖",
        "Backup & Restore": "💾",
        "Settings": "⚙️"
    }
    st.markdown(f"""
    <div style="padding: 10px; background-color: #ffffff; border-radius: 8px; margin-bottom: 20px;">
        <h2 style="display:inline;">🎟️ {st.session_state.company_name} Ticket System</h2>
    </div>
    """, unsafe_allow_html=True)
    cols = st.columns(len(pages))
    for i, (page, icon) in enumerate(pages.items()):
        if cols[i].button(f"{icon} {page}"):
            st.session_state.active_page = page

# -----------------------------------------------------------
# Dashboard Page
# -----------------------------------------------------------
def dashboard_page():
    # Top animation and title
    col_anim, col_title = st.columns([1, 5])
    with col_anim:
        if animations["dashboard"]:
            st_lottie(animations["dashboard"], height=150, key="dash_anim")
    with col_title:
        st.markdown("## 📊 Real-Time Ticket Analytics")
        st.write("View and analyze your ticket performance and earnings at a glance.")
    
    # Totals are computed by summing num_sub_tickets
    cursor.execute("SELECT SUM(num_sub_tickets) FROM tickets WHERE status='Intake'")
    total_intake = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(num_sub_tickets) FROM tickets WHERE status='Return'")
    total_ready = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(num_sub_tickets) FROM tickets WHERE status='Delivered'")
    total_delivered = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(num_sub_tickets) FROM tickets")
    total_overall = cursor.fetchone()[0] or 0

    estimated_earnings = total_intake * st.session_state.ticket_price
    actual_earnings = total_delivered * st.session_state.ticket_price

    # Display key metrics (Overall, Intake, Ready, Delivered)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Overall Total Tickets", f"{int(total_overall)}")
    col2.metric("Total Intake", f"{int(total_intake)}", f"${estimated_earnings:.2f}")
    col3.metric("Ready to Deliver", f"{int(total_ready)}", f"${total_ready * st.session_state.ticket_price:.2f}")
    col4.metric("Total Delivered", f"{int(total_delivered)}", f"${actual_earnings:.2f}")

    # Date Range Analysis
    st.subheader("📅 Date Range Analysis")
    col_date1, col_date2 = st.columns(2)
    with col_date1:
        start_date = st.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
    with col_date2:
        end_date = st.date_input("End Date", datetime.date.today())
    
    query = """
    SELECT date, 
           SUM(CASE WHEN status='Delivered' THEN num_sub_tickets ELSE 0 END) as delivered,
           SUM(CASE WHEN status='Return' THEN num_sub_tickets ELSE 0 END) as ready,
           SUM(CASE WHEN status='Intake' THEN num_sub_tickets ELSE 0 END) as intake
    FROM tickets
    WHERE date BETWEEN ? AND ?
    GROUP BY date
    ORDER BY date
    """
    df_daily = pd.read_sql(query, conn, params=[start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")])
    if not df_daily.empty:
        df_daily['date'] = pd.to_datetime(df_daily['date'])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_daily['date'], y=df_daily['delivered'],
                                 mode='lines+markers', name='Delivered',
                                 line=dict(width=3), fill='tozeroy'))
        fig.add_trace(go.Scatter(x=df_daily['date'], y=df_daily['ready'],
                                 mode='lines+markers', name='Ready to Deliver',
                                 line=dict(width=3)))
        fig.add_trace(go.Scatter(x=df_daily['date'], y=df_daily['intake'],
                                 mode='lines+markers', name='Intake',
                                 line=dict(width=3, dash='dot')))
        fig.update_layout(title='Daily Ticket Activity', 
                          xaxis_title='Date', 
                          yaxis_title='Number of Tickets',
                          hovermode='x unified', 
                          template='plotly_white', 
                          height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        df_daily['delivered_value'] = df_daily['delivered'] * st.session_state.ticket_price
        fig2 = px.bar(df_daily, x='date', y='delivered_value',
                      title="Daily Delivery Earnings",
                      labels={'delivered_value': 'Earnings ($)', 'date': 'Date'})
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No data available for selected date range")
    
    # Performance Statistics: Gauge and Pie Chart
    st.subheader("📈 Performance Statistics")
    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        total_intake = max(total_intake, 0)
        conversion_rate = (total_delivered / total_intake * 100) if total_intake > 0 else 0
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=conversion_rate,
            title={'text': "Delivery Rate"},
            gauge={'axis': {'range': [0, 100]},
                   'bar': {'color': "green"},
                   'steps': [
                       {'range': [0, 33], 'color': "lightgray"},
                       {'range': [33, 66], 'color': "gray"},
                       {'range': [66, 100], 'color': "darkgray"}
                   ]}
        ))
        fig_gauge.update_layout(height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)
    with col_stat2:
        query_status = "SELECT status, COUNT(*) as count FROM tickets GROUP BY status"
        df_status = pd.read_sql(query_status, conn)
        if not df_status.empty:
            # Convert each DB status to display label
            df_status['status_ui'] = df_status['status'].apply(display_status)
            fig_pie = px.pie(df_status, values='count', names='status_ui',
                             title="Ticket Status Distribution")
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(height=300)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No status data available")
    
    # Recent Activity Table
    st.subheader("⏱️ Recent Activity")
    df_recent = pd.read_sql("SELECT date, ticket_number, status, num_sub_tickets FROM tickets ORDER BY date DESC, time DESC LIMIT 8", conn)
    if not df_recent.empty:
        df_recent['status'] = df_recent['status'].apply(display_status)
        st.dataframe(df_recent, use_container_width=True)
    else:
        st.info("No recent activity to display")

# -----------------------------------------------------------
# Add Tickets Page
# -----------------------------------------------------------
def add_tickets_page():
    col_anim, col_title = st.columns([1, 5])
    with col_anim:
        if animations["tickets"]:
            st_lottie(animations["tickets"], height=150, key="ticket_anim")
    with col_title:
        st.markdown("## ➕ Add New Tickets")
        st.write(f"Current ticket price: ${st.session_state.ticket_price:.2f} per sub-ticket")
    
    st.markdown("---")
    col1, col2 = st.columns([2, 1])
    with col1:
        batch_name = st.text_input("Batch Name (optional)", placeholder="Enter a meaningful batch name")
        ticket_input_type = st.radio("Ticket Input Type", ["Multiple/General", "Large Ticket"], horizontal=True)
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        if not batch_name.strip():
            cursor.execute("SELECT COUNT(DISTINCT batch_name) FROM tickets")
            batch_count = cursor.fetchone()[0] + 1
            batch_name = f"{st.session_state.batch_prefix}{batch_count}"
    with col2:
        st.markdown("""
        **Quick Instructions**
        1. Enter a batch name (optional).
        2. Choose an input type.
        3. Enter ticket number(s).
        4. Click the Add button.
        """)
    
    if ticket_input_type == "Multiple/General":
        tickets_text = st.text_area("Enter Ticket Number(s)", placeholder="Space or newline separated ticket numbers")
        if st.button("Add Tickets"):
            if tickets_text.strip():
                tickets_list = tickets_text.replace('\n', ' ').strip().split()
                success_count = 0
                failed_tickets = []
                for t in tickets_list:
                    t = t.strip()
                    if t:
                        try:
                            cursor.execute(
                                """INSERT INTO tickets (date, time, batch_name, ticket_number, num_sub_tickets, status, pay)
                                   VALUES(?,?,?,?,?,?,?)""",
                                (current_date, current_time, batch_name, t, 1, "Intake", st.session_state.ticket_price)
                            )
                            success_count += 1
                        except sqlite3.IntegrityError:
                            failed_tickets.append(t)
                conn.commit()
                if success_count:
                    st.success(f"Successfully added {success_count} ticket(s) to batch '{batch_name}'.")
                    if animations["success"]:
                        st_lottie(animations["success"], height=120)
                if failed_tickets:
                    st.warning(f"Could not add {len(failed_tickets)} ticket(s) because they already exist: {', '.join(failed_tickets[:5])}{'...' if len(failed_tickets) > 5 else ''}")
            else:
                st.warning("Please enter ticket number(s).")
    else:
        col_large1, col_large2 = st.columns(2)
        with col_large1:
            large_ticket = st.text_input("Large Ticket Number", placeholder="Enter the main ticket number")
        with col_large2:
            sub_count = st.number_input("Number of Sub-Tickets", min_value=1, value=5, step=1)
        if st.button("Add Large Ticket"):
            if large_ticket.strip():
                try:
                    cursor.execute(
                        """INSERT INTO tickets (date, time, batch_name, ticket_number, num_sub_tickets, status, pay)
                           VALUES(?,?,?,?,?,?,?)""",
                        (current_date, current_time, batch_name, large_ticket.strip(), sub_count, "Intake", st.session_state.ticket_price)
                    )
                    conn.commit()
                    st.success(f"Added large ticket '{large_ticket}' with {sub_count} sub-tickets to batch '{batch_name}'.")
                    if animations["success"]:
                        st_lottie(animations["success"], height=120)
                except sqlite3.IntegrityError:
                    st.error(f"Ticket '{large_ticket.strip()}' already exists.")
            else:
                st.warning("Please enter a valid ticket number.")
    
    st.markdown("---")
    st.subheader("Recent Additions")
    df_recent = pd.read_sql("SELECT date, time, batch_name, ticket_number, num_sub_tickets, status FROM tickets ORDER BY id DESC LIMIT 5", conn)
    if not df_recent.empty:
        df_recent['status'] = df_recent['status'].apply(display_status)
        st.dataframe(df_recent, use_container_width=True)
    else:
        st.info("No recent tickets added.")

# -----------------------------------------------------------
# View Tickets Page
# -----------------------------------------------------------
def view_tickets_page():
    st.markdown("## 👁️ View Tickets by Status")
    # We'll show only known statuses in separate tabs, plus a "Mixed/Other" if needed
    # But let's focus on "Intake", "Return", "Delivered"
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📥 Intake",
        "🔄 Ready to Deliver",
        "🚚 Delivered",
        "On Hold",
        "Cancelled"
    ])
    
    # For each known status, query and show
    def show_status_data(status_key, container):
        with container:
            st.subheader(f"Tickets with status '{display_status(status_key)}'")
            df_data = pd.read_sql("SELECT * FROM tickets WHERE status=? ORDER BY date DESC, time DESC", conn, params=(status_key,))
            if not df_data.empty:
                df_data['status'] = df_data['status'].apply(display_status)
                st.dataframe(df_data, use_container_width=True)
                total_count = df_data['num_sub_tickets'].sum()
                total_value = total_count * st.session_state.ticket_price
                colA, colB = st.columns(2)
                colA.metric("Total Sub-Tickets", f"{int(total_count)}")
                colB.metric("Total Value", f"${total_value:,.2f}")
            else:
                st.info(f"No tickets found with status '{display_status(status_key)}'")

    # Intake
    show_status_data("Intake", tab1)
    # Ready (Return)
    show_status_data("Return", tab2)
    # Delivered
    show_status_data("Delivered", tab3)
    # On Hold
    show_status_data("On Hold", tab4)
    # Cancelled
    show_status_data("Cancelled", tab5)

# -----------------------------------------------------------
# Manage Tickets Page
# -----------------------------------------------------------
def manage_tickets_page():
    col_anim, col_title = st.columns([1, 5])
    with col_anim:
        if animations["settings"]:
            st_lottie(animations["settings"], height=150, key="manage_anim")
    with col_title:
        st.markdown("## 🔄 Manage Tickets")
        st.write("Advanced ticket management operations")
    
    st.markdown("---")
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 Search & Edit",
        "⚡ Bulk Operations",
        "🗑️ Delete Tickets",
        "📦 By Batch",
        "💻 SQL Query"
    ])
    
    # Tab 1: Search & Edit (Individual Ticket)
    with tab1:
        st.subheader("Individual Ticket Management")
        ticket_number = st.text_input("Enter Ticket Number to Manage")
        if ticket_number:
            ticket_data = pd.read_sql("SELECT * FROM tickets WHERE ticket_number = ?", conn, params=(ticket_number.strip(),))
            if not ticket_data.empty:
                current_status_db = ticket_data.iloc[0]['status']
                current_status_ui = display_status(current_status_db)
                
                # Build a status selectbox from the display labels
                status_display_list = [display_status(s) for s in AVAILABLE_STATUSES]
                default_idx = status_display_list.index(current_status_ui) if current_status_ui in status_display_list else 0
                
                with st.form("edit_ticket_form"):
                    new_status_label = st.selectbox("Status", status_display_list, index=default_idx)
                    new_status_db = get_db_status_from_display(new_status_label)
                    new_subtickets = st.number_input("Sub-Tickets", min_value=1, value=int(ticket_data.iloc[0]['num_sub_tickets']))
                    new_price = st.number_input("Ticket Price", min_value=0.0, value=float(ticket_data.iloc[0]['pay']), step=0.5)
                    if st.form_submit_button("Update Ticket"):
                        cursor.execute(
                            "UPDATE tickets SET status = ?, num_sub_tickets = ?, pay = ? WHERE ticket_number = ?",
                            (new_status_db, new_subtickets, new_price, ticket_number.strip())
                        )
                        conn.commit()
                        st.success("Ticket updated successfully!")
                        if animations["success"]:
                            st_lottie(animations["success"], height=80)
            else:
                st.warning("Ticket not found in database")
    
    # Tab 2: Bulk Operations
    with tab2:
        st.subheader("Bulk Operations")
        bulk_tickets = st.text_area("Enter Ticket Numbers (one per line)", help="Enter one ticket number per line")
        bulk_action = st.selectbox("Action", ["Update Status", "Change Price", "Add Subtickets"])
        if bulk_tickets:
            ticket_list = [t.strip() for t in bulk_tickets.split('\n') if t.strip()]
            found_tickets = []
            missing_tickets = []
            for t in ticket_list:
                cursor.execute("SELECT 1 FROM tickets WHERE ticket_number = ?", (t,))
                if cursor.fetchone():
                    found_tickets.append(t)
                else:
                    missing_tickets.append(t)
            if missing_tickets:
                st.warning(f"{len(missing_tickets)} tickets not found: {', '.join(missing_tickets[:3])}{'...' if len(missing_tickets) > 3 else ''}")
            if found_tickets:
                st.success(f"{len(found_tickets)} valid tickets found")
                if bulk_action == "Update Status":
                    status_display_list = [display_status(s) for s in AVAILABLE_STATUSES]
                    new_status_label = st.selectbox("New Status", status_display_list)
                    new_status_db = get_db_status_from_display(new_status_label)
                    if st.button("Update Status for All Found Tickets"):
                        for t in found_tickets:
                            cursor.execute("UPDATE tickets SET status = ? WHERE ticket_number = ?", (new_status_db, t))
                        conn.commit()
                        st.success(f"Updated {len(found_tickets)} tickets to {new_status_label} status")
                elif bulk_action == "Change Price":
                    new_price = st.number_input("New Price", min_value=0.0, value=st.session_state.ticket_price)
                    if st.button("Update Price for All Found Tickets"):
                        for t in found_tickets:
                            cursor.execute("UPDATE tickets SET pay = ? WHERE ticket_number = ?", (new_price, t))
                        conn.commit()
                        st.success(f"Updated pricing for {len(found_tickets)} tickets")
                elif bulk_action == "Add Subtickets":
                    add_count = st.number_input("Additional Subtickets", min_value=1, value=1)
                    if st.button("Add Subtickets to All Found Tickets"):
                        for t in found_tickets:
                            cursor.execute("UPDATE tickets SET num_sub_tickets = num_sub_tickets + ? WHERE ticket_number = ?", (add_count, t))
                        conn.commit()
                        st.success(f"Added {add_count} subtickets to {len(found_tickets)} tickets")
    
    # Tab 3: Delete Tickets
    with tab3:
        st.subheader("Ticket Deletion")
        delete_option = st.radio("Deletion Method", ["Single Ticket", "By Batch", "By Date Range"])
        if delete_option == "Single Ticket":
            del_ticket = st.text_input("Enter Ticket Number to Delete")
            if del_ticket and st.button("Delete Ticket"):
                cursor.execute("DELETE FROM tickets WHERE ticket_number = ?", (del_ticket.strip(),))
                conn.commit()
                if cursor.rowcount > 0:
                    st.success("Ticket deleted successfully")
                else:
                    st.error("Ticket not found")
        elif delete_option == "By Batch":
            batch_name = st.text_input("Enter Batch Name to Delete")
            if batch_name and st.button("Delete Entire Batch"):
                cursor.execute("DELETE FROM tickets WHERE batch_name = ?", (batch_name.strip(),))
                conn.commit()
                st.success(f"Deleted {cursor.rowcount} tickets from batch {batch_name}")
        elif delete_option == "By Date Range":
            col_date1, col_date2 = st.columns(2)
            with col_date1:
                start_date = st.date_input("Start Date")
            with col_date2:
                end_date = st.date_input("End Date")
            if st.button("Delete Tickets in Date Range"):
                cursor.execute("DELETE FROM tickets WHERE date BETWEEN ? AND ?", (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
                conn.commit()
                st.success(f"Deleted {cursor.rowcount} tickets from {start_date} to {end_date}")
    
    # Tab 4: Manage Tickets By Batch
    with tab4:
        st.subheader("Manage Tickets By Batch Name")
        cursor.execute("SELECT DISTINCT batch_name FROM tickets")
        batch_rows = cursor.fetchall()
        batch_names = [row[0] for row in batch_rows if row[0]]
        if batch_names:
            selected_batch = st.selectbox("Select a Batch to Manage", batch_names)
            if selected_batch:
                df_batch = pd.read_sql("SELECT * FROM tickets WHERE batch_name = ?", conn, params=(selected_batch,))
                df_batch['status'] = df_batch['status'].apply(display_status)
                st.dataframe(df_batch, use_container_width=True)

                # Bulk update of the entire batch to a single status
                status_display_list = [display_status(s) for s in AVAILABLE_STATUSES]
                new_status_label = st.selectbox("New Status for All Tickets in This Batch", status_display_list)
                new_status_db = get_db_status_from_display(new_status_label)
                if st.button("Update All Tickets in Batch"):
                    cursor.execute("UPDATE tickets SET status = ? WHERE batch_name = ?", (new_status_db, selected_batch))
                    conn.commit()
                    st.success(f"All tickets in batch '{selected_batch}' updated to '{new_status_label}'!")
                    
                    # Show updated data
                    df_batch = pd.read_sql("SELECT * FROM tickets WHERE batch_name = ?", conn, params=(selected_batch,))
                    df_batch['status'] = df_batch['status'].apply(display_status)
                    st.dataframe(df_batch, use_container_width=True)
        else:
            st.info("No batches found in the database.")
    
    # Tab 5: Custom SQL Query Insert/Update
    with tab5:
        st.subheader("Custom SQL Query Insert/Update")
        st.write("Enter a valid SQL query (only INSERT or UPDATE queries are allowed) to update the tickets table. "
                 "This will modify ticket records and changes will reflect in the Intake, Ready to Deliver, and Delivered views.")
        sql_query = st.text_area("SQL Query", height=150,
                                 placeholder="e.g., INSERT INTO tickets (date, time, batch_name, ticket_number, num_sub_tickets, status, pay) VALUES ('2025-03-24', '12:34:56', 'Batch-100', 'TICKET123', 1, 'Intake', 5.5)")
        if st.button("Execute SQL Query"):
            if sql_query.strip():
                try:
                    cursor.execute(sql_query)
                    conn.commit()
                    st.success(f"Query executed successfully. Rows affected: {cursor.rowcount}")
                except Exception as e:
                    st.error(f"Error executing query: {e}")
            else:
                st.warning("Please enter a SQL query.")
    
    st.markdown("---")

# -----------------------------------------------------------
# BULK TICKET COMPARISON PAGE
# -----------------------------------------------------------
def bulk_ticket_comparison_page():
    st.markdown("## 🔍 Bulk Ticket Comparison")
    st.write("""
        Paste a list of ticket numbers (one per line) to see how they compare 
        with tickets in the database:
        - **Missing in DB**: In your pasted list but not in the DB.
        - **Extra in DB**: In the DB but not in your pasted list.
        - **Matches**: Found in both.
    """)

    pasted_tickets_text = st.text_area(
        "Paste ticket numbers here (one per line)",
        height=200,
        placeholder="e.g.\n12345\n12346\nABC999"
    )

    if st.button("Compare"):
        user_tickets = set()
        lines = pasted_tickets_text.strip().splitlines()
        for line in lines:
            line = line.strip()
            if line:
                user_tickets.add(line)

        if not user_tickets:
            st.warning("No valid ticket numbers found in the text area.")
            return

        df_db_tickets = pd.read_sql("SELECT ticket_number FROM tickets", conn)
        db_tickets = set(df_db_tickets["ticket_number"].tolist())

        missing_in_db = user_tickets - db_tickets
        extra_in_db = db_tickets - user_tickets
        matches = user_tickets & db_tickets

        colA, colB, colC = st.columns(3)
        colA.metric("Missing in DB", len(missing_in_db))
        colB.metric("Extra in DB", len(extra_in_db))
        colC.metric("Matches", len(matches))

        st.write("---")
        st.subheader("Details")

        if missing_in_db:
            st.write("### Tickets Missing in DB")
            st.write(", ".join(sorted(missing_in_db)))
        else:
            st.info("No missing tickets in DB.")

        if extra_in_db:
            st.write("### Tickets in DB But Not in Your List")
            st.write(", ".join(sorted(extra_in_db)))
            placeholders = ",".join(["?"] * len(extra_in_db))
            query_extra = f"SELECT * FROM tickets WHERE ticket_number IN ({placeholders})"
            df_extra = pd.read_sql(query_extra, conn, params=list(extra_in_db))
            df_extra["status"] = df_extra["status"].apply(display_status)
            st.dataframe(df_extra, use_container_width=True)
        else:
            st.info("No extra tickets found in DB.")

        if matches:
            st.write("### Matched Tickets (In Both Lists)")
            placeholders = ",".join(["?"] * len(matches))
            query = f"SELECT * FROM tickets WHERE ticket_number IN ({placeholders})"
            df_matched = pd.read_sql(query, conn, params=list(matches))
            df_matched["status"] = df_matched["status"].apply(display_status)
            st.dataframe(df_matched, use_container_width=True)
        else:
            st.info("No tickets were found in both lists.")

# -----------------------------------------------------------
# SQL Query Converter Page
# -----------------------------------------------------------
def sql_query_converter_page():
    st.markdown("## SQL Query Converter")
    st.write("Paste your raw ticket data (each line should be in the format `TicketNumber - Description`) and choose a target status. "
             "This tool will extract the ticket numbers and update or insert them into the database as needed.")
    
    raw_text = st.text_area("Enter raw ticket data", placeholder="""125633 - Eastport-South Manor / Acer R752T
125632 - Eastport-South Manor / Acer R752T
125631 - Eastport-South Manor / Acer R752T""", height=200)
    
    # Let user pick any known status from our global list
    display_list = [display_status(s) for s in AVAILABLE_STATUSES]
    target_status_label = st.selectbox("Select target status", display_list)
    target_status_db = get_db_status_from_display(target_status_label)
    
    if st.button("Generate and Execute SQL Query"):
        lines = raw_text.strip().splitlines()
        ticket_numbers = []
        for line in lines:
            line = line.strip()
            if " - " in line:
                tnum = line.split(" - ")[0].strip()
                ticket_numbers.append(tnum)
            else:
                # Fallback: take the first word of the line, if any
                parts = line.split()
                if parts:
                    ticket_numbers.append(parts[0].strip())

        if ticket_numbers:
            # We'll do two steps:
            # 1) INSERT OR IGNORE any that don't exist
            # 2) UPDATE status
            now_date = datetime.datetime.now().strftime("%Y-%m-%d")
            now_time = datetime.datetime.now().strftime("%H:%M:%S")
            insert_sql = """
                INSERT OR IGNORE INTO tickets (date, time, batch_name, ticket_number, num_sub_tickets, status, pay)
                VALUES (?, ?, ?, ?, 1, 'Intake', ?)
            """
            for tkt in ticket_numbers:
                try:
                    cursor.execute(insert_sql, (now_date, now_time, "Auto-Batch", tkt, st.session_state.ticket_price))
                except Exception as e:
                    st.error(f"Error inserting ticket {tkt}: {e}")
            conn.commit()

            # 2) Update to the chosen status
            placeholders = ",".join(["?"] * len(ticket_numbers))
            update_sql = f"UPDATE tickets SET status = ? WHERE ticket_number IN ({placeholders})"
            params = [target_status_db] + ticket_numbers
            try:
                cursor.execute(update_sql, params)
                conn.commit()
                st.success(
                    f"Inserted/updated {cursor.rowcount} tickets to '{target_status_label}'."
                )
            except Exception as e:
                st.error(f"Error updating tickets to '{target_status_label}': {e}")
        else:
            st.warning("No ticket numbers found in the input.")

# -----------------------------------------------------------
# Batches Page (revised to handle single-status vs mixed)
# -----------------------------------------------------------
def batch_view_page():
    st.markdown("## 🗂️ Batch View")
    st.write("""Each batch is shown under the tab that matches its **single** status. 
    If a batch has multiple ticket statuses, it is shown as "Mixed" in the Mixed tab.""")
    
    df_batches = pd.read_sql(
        """
        SELECT batch_name, 
               GROUP_CONCAT(DISTINCT status) as statuses,
               SUM(num_sub_tickets) as total_tickets,
               GROUP_CONCAT(ticket_number) as ticket_numbers
        FROM tickets
        GROUP BY batch_name
        """, conn
    )
    if df_batches.empty:
        st.info("No batches found.")
        return
    
    # Compute whether each batch has exactly 1 status or multiple
    def get_batch_primary_status(row):
        stat_list = row["statuses"].split(",")
        stat_list = list(set(stat_list))  # unique
        if len(stat_list) == 1:
            return stat_list[0]  # the single status
        return "Mixed"

    df_batches["batch_status"] = df_batches.apply(get_batch_primary_status, axis=1)

    # We create a tab for each known status + a "Mixed" tab
    known_statuses = AVAILABLE_STATUSES + ["Mixed"]
    tab_objects = st.tabs([display_status(s) for s in known_statuses])

    # Helper function to display batch tiles in a given container
    def display_batches_in_tab(df, container, tab_status):
        with container:
            # Filter by that status
            df_filtered = df[df["batch_status"] == tab_status]
            if df_filtered.empty:
                st.info(f"No batches with status '{display_status(tab_status)}'")
                return

            # We'll show them in columns of 3
            cols = st.columns(3)
            for idx, row in df_filtered.iterrows():
                bname = row["batch_name"]
                statuses_raw = row["statuses"]
                total_tickets = row["total_tickets"]
                tnumbers = row["ticket_numbers"]

                # If there's exactly 1 status, display the label; else "Mixed"
                if statuses_raw and "," in statuses_raw:
                    # multiple distinct statuses
                    status_label = "Mixed"
                else:
                    status_label = display_status(statuses_raw)

                with cols[idx % 3]:
                    st.markdown(f"""
                    <div style="border: 1px solid #ccc; border-radius: 8px; padding: 10px; margin: 5px; text-align: center;">
                        <h4>{bname}</h4>
                        <p>Total Tickets: {total_tickets}</p>
                        <p>Status: {status_label}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button(f"Edit Status - {bname}", key=f"edit_btn_{bname}_{tab_status}"):
                        st.session_state["edit_batch"] = bname
                        st.session_state["edit_batch_status"] = status_label

                    if st.button(f"Copy Tickets - {bname}", key=f"copy_btn_{bname}_{tab_status}"):
                        # Simple approach: show them in an expander, or copy via HTML
                        # We'll do the same HTML/JS approach for direct copying:
                        random_suffix = f"copy_{bname}_{tab_status}"
                        html_code = f"""
                        <input id="copyInput_{random_suffix}" 
                            type="text" 
                            value="{tnumbers}" 
                            style="opacity: 0; position: absolute; left: -9999px;">
                        <button onclick="copyText_{random_suffix}()">Click to Copy Tickets</button>
                        <script>
                        function copyText_{random_suffix}() {{
                            var copyText = document.getElementById("copyInput_{random_suffix}");
                            copyText.select();
                            document.execCommand("copy");
                            alert("Copied tickets: " + copyText.value);
                        }}
                        </script>
                        """
                        components.html(html_code, height=50)
    
    # Create sub-tabs for each known status
    for status_key, tab_obj in zip(known_statuses, tab_objects):
        display_batches_in_tab(df_batches, tab_obj, status_key)

    # If user clicked "Edit Status" for a batch, show an update form at bottom
    if "edit_batch" in st.session_state and st.session_state["edit_batch"]:
        bname = st.session_state["edit_batch"]
        st.markdown("---")
        st.markdown(f"## Update Batch Status for: **{bname}**")
        df_b = pd.read_sql("SELECT * FROM tickets WHERE batch_name = ?", conn, params=(bname,))
        st.dataframe(df_b, use_container_width=True)

        # Let user pick new status
        status_display_list = [display_status(s) for s in AVAILABLE_STATUSES]
        new_status_label = st.selectbox("New Status", status_display_list)
        new_status_db = get_db_status_from_display(new_status_label)

        if st.button("Confirm Status Update"):
            cursor.execute("UPDATE tickets SET status = ? WHERE batch_name = ?", (new_status_db, bname))
            conn.commit()
            st.success(f"All tickets in batch '{bname}' updated to '{new_status_label}'.")
            # Clear from session
            st.session_state["edit_batch"] = None
            st.session_state["edit_batch_status"] = None
            st.experimental_rerun()

# -----------------------------------------------------------
# Income Page
# -----------------------------------------------------------
def income_page():
    col_anim, col_title = st.columns([1, 5])
    with col_anim:
        if animations["money"]:
            st_lottie(animations["money"], height=150, key="money_anim")
    with col_title:
        st.markdown("## 💰 Income Analysis")
        st.write("Track, analyze, and forecast your earnings from delivered tickets. View both the received income and potential income from pending tickets.")
    
    st.markdown("---")
    col_date1, col_date2 = st.columns(2)
    with col_date1:
        start_date = st.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
    with col_date2:
        end_date = st.date_input("End Date", datetime.date.today())
    
    query_delivered = """
        SELECT date,
               SUM(num_sub_tickets * pay) AS day_earnings
        FROM tickets
        WHERE status='Delivered' AND date BETWEEN ? AND ?
        GROUP BY date
        ORDER BY date ASC
    """
    df_income = pd.read_sql(query_delivered, conn, params=[start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")])
    
    query_pending = """
        SELECT SUM(num_sub_tickets * pay) AS pending_income
        FROM tickets
        WHERE status != 'Delivered'
    """
    df_pending = pd.read_sql(query_pending, conn)
    pending_income = df_pending.iloc[0]['pending_income'] or 0

    if not df_income.empty:
        df_income['date'] = pd.to_datetime(df_income['date'])
        df_income.sort_values("date", inplace=True)
        
        fig = px.area(df_income, x="date", y="day_earnings", title="Daily Earnings Trend",
                      labels={"day_earnings": "Earnings ($)", "date": "Date"})
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Detailed Earnings")
        st.dataframe(df_income, use_container_width=True)
        
        total_received = df_income["day_earnings"].sum()
        st.metric("Amount Received", f"${total_received:,.2f}")
        st.metric("Pending Income", f"${pending_income:,.2f}")
        st.metric("Total Potential Income", f"${total_received + pending_income:,.2f}")
        
        # Simple linear forecast
        if len(df_income) > 1:
            df_income["date_num"] = df_income["date"].map(datetime.datetime.toordinal)
            x = df_income["date_num"].values
            y = df_income["day_earnings"].values
            coeffs = np.polyfit(x, y, 1)
            poly = np.poly1d(coeffs)
            last_date = df_income["date"].max()
            forecast_dates = [last_date + datetime.timedelta(days=i) for i in range(1, 8)]
            forecast_x = [d.toordinal() for d in forecast_dates]
            forecast_y = poly(forecast_x)
            
            fig.add_trace(go.Scatter(x=forecast_dates, y=forecast_y, mode='lines+markers', name="Forecast"))
            st.plotly_chart(fig, use_container_width=True)
            
            st.write("Forecast for the next 7 days (based on a simple linear trend):")
            forecast_df = pd.DataFrame({
                "Date": forecast_dates,
                "Forecasted Earnings ($)": np.round(forecast_y, 2)
            })
            st.dataframe(forecast_df)
        else:
            st.info("Not enough data for forecasting.")
    else:
        st.info("No delivered tickets found in this date range")
    
    st.markdown("---")

# -----------------------------------------------------------
# AI Analysis Page
# -----------------------------------------------------------
def ai_analysis_page():
    st.markdown("## 🤖 AI Analysis")
    st.write("This section provides AI-driven insights into your ticket management performance based on historical data. "
             "It can highlight trends, perform simple forecasts, and detect anomalies in your delivered ticket counts.")
    
    total_tickets_df = pd.read_sql("SELECT SUM(num_sub_tickets) as total FROM tickets", conn)
    total_tickets = total_tickets_df.iloc[0]['total'] or 0
    total_delivered_df = pd.read_sql("SELECT SUM(num_sub_tickets) as total_delivered FROM tickets WHERE status='Delivered'", conn)
    total_delivered = total_delivered_df.iloc[0]['total_delivered'] or 0
    conversion_rate = (total_delivered / total_tickets * 100) if total_tickets else 0

    st.metric("Total Tickets", total_tickets)
    st.metric("Total Delivered", total_delivered)
    st.metric("Delivery Conversion Rate (%)", f"{conversion_rate:.2f}%")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Daily Trend & Forecast", "Weekday Analysis", "Calendar Heatmap", "Anomaly Detection"])
    
    with tab1:
        df_trend = pd.read_sql(
            "SELECT date, SUM(num_sub_tickets) as delivered FROM tickets WHERE status='Delivered' GROUP BY date ORDER BY date",
            conn
        )
        if not df_trend.empty:
            df_trend['date'] = pd.to_datetime(df_trend['date'])
            fig1 = go.Figure(go.Scatter(x=df_trend['date'], y=df_trend['delivered'], mode='lines+markers', name="Historical"))
            fig1.update_layout(title="Daily Delivered Tickets Trend", xaxis_title="Date", yaxis_title="Delivered Tickets")
            st.plotly_chart(fig1, use_container_width=True)
            avg_delivered = df_trend['delivered'].mean()
            st.write(f"On average, you deliver about {avg_delivered:.1f} tickets per day.")
            
            df_trend = df_trend.sort_values("date")
            df_trend["date_num"] = df_trend["date"].map(datetime.datetime.toordinal)
            x = df_trend["date_num"].values
            y = df_trend["delivered"].values
            if len(x) > 1:
                coeffs = np.polyfit(x, y, 1)
                poly = np.poly1d(coeffs)
                last_date = df_trend["date"].max()
                forecast_dates = [last_date + datetime.timedelta(days=i) for i in range(1, 8)]
                forecast_x = [d.toordinal() for d in forecast_dates]
                forecast_y = poly(forecast_x)
                fig1.add_trace(go.Scatter(x=forecast_dates, y=forecast_y, mode='lines+markers', name="Forecast"))
                st.plotly_chart(fig1, use_container_width=True)
                st.write("Forecast for the next 7 days (based on a simple linear trend):")
                forecast_df = pd.DataFrame({
                    "Date": forecast_dates,
                    "Forecasted Delivered Tickets": np.round(forecast_y, 1)
                })
                st.dataframe(forecast_df)
            else:
                st.info("Not enough data for forecasting.")
        else:
            st.info("No delivered ticket data available for daily trend analysis.")
    
    with tab2:
        df_status = pd.read_sql(
            "SELECT date, status, SUM(num_sub_tickets) as count FROM tickets GROUP BY date, status",
            conn
        )
        if not df_status.empty:
            df_status['date'] = pd.to_datetime(df_status['date'])
            df_status['weekday'] = df_status['date'].dt.day_name()
            df_status['status_ui'] = df_status['status'].apply(display_status)
            pivot = df_status.pivot_table(index='weekday', columns='status_ui', values='count', aggfunc='mean', fill_value=0)
            weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            pivot = pivot.reindex(weekday_order)
            st.subheader("Average Daily Ticket Counts by Weekday")
            st.dataframe(pivot)
            fig2 = go.Figure()
            for status_col in pivot.columns:
                fig2.add_trace(go.Bar(
                    x=pivot.index,
                    y=pivot[status_col],
                    name=status_col
                ))
            fig2.update_layout(
                title="Average Ticket Counts by Weekday",
                xaxis_title="Weekday",
                yaxis_title="Average Count",
                barmode="group"
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No ticket data available for weekday analysis.")
    
    with tab3:
        df_delivered = pd.read_sql("SELECT date, SUM(num_sub_tickets) as delivered FROM tickets WHERE status='Delivered' GROUP BY date", conn)
        if not df_delivered.empty:
            df_delivered['date'] = pd.to_datetime(df_delivered['date'])
            df_delivered['week'] = df_delivered['date'].dt.isocalendar().week
            df_delivered['weekday'] = df_delivered['date'].dt.day_name()
            weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            heatmap_data = df_delivered.pivot_table(index='weekday', columns='week', values='delivered', fill_value=0)
            heatmap_data = heatmap_data.reindex(weekday_order)
            st.subheader("Calendar Heatmap of Delivered Tickets")
            fig3 = go.Figure(data=go.Heatmap(
                z=heatmap_data.values,
                x=heatmap_data.columns,
                y=heatmap_data.index,
                colorscale='Viridis'
            ))
            fig3.update_layout(title="Delivered Tickets Heatmap", xaxis_title="Week Number", yaxis_title="Weekday")
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No delivered ticket data available for calendar heatmap.")
    
    with tab4:
        df_anomaly = pd.read_sql("SELECT date, SUM(num_sub_tickets) as delivered FROM tickets WHERE status='Delivered' GROUP BY date", conn)
        if not df_anomaly.empty:
            df_anomaly['date'] = pd.to_datetime(df_anomaly['date'])
            mean_val = df_anomaly['delivered'].mean()
            std_val = df_anomaly['delivered'].std()
            df_anomaly['anomaly'] = df_anomaly['delivered'].apply(
                lambda x: 'Yes' if (x > mean_val + 2*std_val or x < mean_val - 2*std_val) else 'No'
            )
            st.subheader("Anomaly Detection in Delivered Tickets")
            st.write(f"Mean: {mean_val:.1f}, Standard Deviation: {std_val:.1f}")
            st.dataframe(df_anomaly)
            fig4 = go.Figure()
            fig4.add_trace(go.Scatter(
                x=df_anomaly['date'],
                y=df_anomaly['delivered'],
                mode='lines+markers',
                name="Delivered"
            ))
            anomalies = df_anomaly[df_anomaly['anomaly'] == 'Yes']
            if not anomalies.empty:
                fig4.add_trace(go.Scatter(
                    x=anomalies['date'],
                    y=anomalies['delivered'],
                    mode='markers',
                    marker=dict(color='red', size=10),
                    name="Anomalies"
                ))
            fig4.update_layout(
                title="Delivered Tickets with Anomalies",
                xaxis_title="Date",
                yaxis_title="Delivered Tickets"
            )
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No delivered ticket data available for anomaly detection.")
    
    st.subheader("Recommendations")
    if conversion_rate < 50:
        st.info("Your delivery conversion rate is below 50%. Consider strategies to improve ticket delivery, such as follow-up reminders or quality control checks.")
    elif conversion_rate < 75:
        st.info("Your delivery conversion rate is moderate. There might be room for improvement to achieve higher efficiency.")
    else:
        st.success("Great job! Your delivery conversion rate is high, indicating efficient ticket management.")
    
    st.write("Keep monitoring your performance regularly to identify trends and optimize your operations.")

# -----------------------------------------------------------
# Backup & Restore Page
# -----------------------------------------------------------
def backup_restore_page():
    global conn
    st.markdown("## 💾 Backup & Restore")
    st.write("Download your database backup or export your ticket data to Excel. You can also restore your ticket data from an Excel file or a .db file.")
    
    st.subheader("Download Options")
    try:
        with open("ticket_management.db", "rb") as db_file:
            db_bytes = db_file.read()
        st.download_button("Download Database (.db)", db_bytes, file_name="ticket_management.db", mime="application/octet-stream")
    except Exception as e:
        st.error("Database file not found.")
    
    df_tickets = pd.read_sql("SELECT * FROM tickets", conn)
    if not df_tickets.empty:
        towrite = BytesIO()
        with pd.ExcelWriter(towrite, engine="xlsxwriter") as writer:
            df_tickets.to_excel(writer, index=False, sheet_name="Tickets")
        towrite.seek(0)
        st.download_button("Download Excel Backup", towrite.read(), file_name="tickets_backup.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("No ticket data available to export.")
    
    st.markdown("---")
    st.subheader("Restore from Excel")
    st.write("Upload an Excel file to restore your ticket data. **Warning:** This will overwrite your current ticket data.")
    uploaded_excel = st.file_uploader("Choose an Excel file", type=["xlsx"])
    if uploaded_excel is not None:
        try:
            df_restore = pd.read_excel(uploaded_excel)
            required_columns = {"date", "time", "batch_name", "ticket_number", "num_sub_tickets", "status", "pay", "comments", "ticket_day", "ticket_school"}
            if not required_columns.issubset(set(df_restore.columns)):
                st.error("Uploaded Excel file does not contain the required columns.")
            else:
                cursor.execute("DELETE FROM tickets")
                conn.commit()
                df_restore.to_sql("tickets", conn, if_exists="append", index=False)
                st.success("Database restored successfully from Excel file!")
        except Exception as e:
            st.error(f"Error restoring from Excel: {e}")
    
    st.markdown("---")
    st.subheader("Restore Database from .db File")
    st.write("Upload a .db file to restore your entire database. **Warning:** This will overwrite your current database.")
    uploaded_db = st.file_uploader("Choose a .db file", type=["db"])
    if uploaded_db is not None:
        try:
            with open("ticket_management.db", "wb") as f:
                f.write(uploaded_db.getbuffer())
            st.success("Database restored successfully from uploaded .db file!")
            conn.close()
            conn = get_db_connection()
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Error restoring database from .db file: {e}")

# -----------------------------------------------------------
# Settings Page
# -----------------------------------------------------------
def settings_page():
    col_anim, col_title = st.columns([1, 5])
    with col_anim:
        if animations["settings"]:
            st_lottie(animations["settings"], height=150, key="settings_anim")
    with col_title:
        st.markdown("## ⚙️ System Settings")
        st.write("Configure application preferences and defaults")
    
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["💰 Pricing", "🏢 Company", "🎨 Appearance"])
    with tab1:
        st.subheader("Ticket Pricing")
        new_price = st.number_input("Price per Sub-Ticket (USD)", min_value=0.0, value=st.session_state.ticket_price, step=0.5)
        if st.button("Update Pricing"):
            st.session_state.ticket_price = new_price
            st.success("Pricing updated successfully!")
    with tab2:
        st.subheader("Company Information")
        company_name = st.text_input("Company Name", value=st.session_state.company_name)
        batch_prefix = st.text_input("Batch Prefix", value=st.session_state.batch_prefix)
        if st.button("Update Company Info"):
            st.session_state.company_name = company_name.strip()
            st.session_state.batch_prefix = batch_prefix.strip()
            st.success("Company information updated!")
    with tab3:
        st.subheader("Appearance Settings")
        dark_mode = st.checkbox("Enable Dark Mode", value=st.session_state.dark_mode)
        if dark_mode != st.session_state.dark_mode:
            st.session_state.dark_mode = dark_mode
            load_css()
        # The color picker is not actively used to style the entire app,
        # but you could incorporate it if you want more advanced theming
        st.color_picker("Primary Color", value="#4CAF50", key="primary_color")
    
    st.markdown("---")

# -----------------------------------------------------------
# Main App Flow
# -----------------------------------------------------------
def main():
    render_navbar()
    pages = {
        "Dashboard": dashboard_page,
        "Add Tickets": add_tickets_page,
        "View Tickets": view_tickets_page,
        "Manage Tickets": manage_tickets_page,
        "Bulk Ticket Comparison": bulk_ticket_comparison_page,
        "SQL Query Converter": sql_query_converter_page,
        "Income": income_page,
        "Batches": batch_view_page,
        "AI Analysis": ai_analysis_page,
        "Backup & Restore": backup_restore_page,
        "Settings": settings_page
    }
    active_page = st.session_state.active_page
    if active_page in pages:
        pages[active_page]()
    st.markdown(f"""
    <div style="text-align:center; padding: 15px; font-size: 0.8rem; border-top: 1px solid #ccc; margin-top: 30px;">
        <p>{st.session_state.company_name} Ticket System • {datetime.datetime.now().year}</p>
        <p>Powered by Streamlit • v1.0</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
