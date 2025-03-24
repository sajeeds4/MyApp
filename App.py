import streamlit as st
import sqlite3
import pandas as pd
import datetime
import requests
from streamlit_lottie import st_lottie
import plotly.express as px
import plotly.graph_objects as go

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
        -- In the DB, "Return" means the ticket is ready to deliver.
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
# Utility: Status Mapping (DB ↔ UI)
# -----------------------------------------------------------
def db_status_from_ui(status_ui: str) -> str:
    """Convert the user-facing status to the DB value."""
    if status_ui == "Ready to Deliver":
        return "Return"
    return status_ui

def ui_status_from_db(status_db: str) -> str:
    """Convert the DB status to the user-facing label."""
    if status_db == "Return":
        return "Ready to Deliver"
    return status_db

# -----------------------------------------------------------
# Navigation (Add "Batches" page to navigation)
# -----------------------------------------------------------
def render_navbar():
    pages = {
        "Dashboard": "📊",
        "Add Tickets": "➕",
        "View Tickets": "👁️",
        "Manage Tickets": "🔄",
        "Income": "💰",
        "Batches": "🗂️",
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
                                   line=dict(color='#2196F3', width=3), fill='tozeroy'))
        fig.add_trace(go.Scatter(x=df_daily['date'], y=df_daily['ready'],
                                   mode='lines+markers', name='Ready to Deliver',
                                   line=dict(color='#FF9800', width=3)))
        fig.add_trace(go.Scatter(x=df_daily['date'], y=df_daily['intake'],
                                   mode='lines+markers', name='Intake',
                                   line=dict(color='#4CAF50', width=3, dash='dot')))
        fig.update_layout(title='Daily Ticket Activity', xaxis_title='Date', yaxis_title='Number of Tickets',
                          hovermode='x unified', template='plotly_white', height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        df_daily['delivered_value'] = df_daily['delivered'] * st.session_state.ticket_price
        fig2 = px.bar(df_daily, x='date', y='delivered_value',
                      title="Daily Delivery Earnings",
                      labels={'delivered_value': 'Earnings ($)', 'date': 'Date'},
                      color_discrete_sequence=['#4CAF50'])
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
                   'bar': {'color': "#4CAF50"},
                   'steps': [{'range': [0, 33], 'color': "#FFCDD2"},
                             {'range': [33, 66], 'color': "#FFECB3"},
                             {'range': [66, 100], 'color': "#C8E6C9"}]}
        ))
        fig_gauge.update_layout(height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)
    with col_stat2:
        query_status = "SELECT status, COUNT(*) as count FROM tickets GROUP BY status"
        df_status = pd.read_sql(query_status, conn)
        if not df_status.empty:
            df_status['status_ui'] = df_status['status'].apply(ui_status_from_db)
            fig_pie = px.pie(df_status, values='count', names='status_ui',
                             title="Ticket Status Distribution",
                             color='status_ui',
                             color_discrete_map={'Intake': '#4CAF50',
                                                 'Ready to Deliver': '#FF9800',
                                                 'Delivered': '#2196F3'})
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(height=300)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No status data available")
    
    # Recent Activity Table
    st.subheader("⏱️ Recent Activity")
    df_recent = pd.read_sql("SELECT date, ticket_number, status, num_sub_tickets FROM tickets ORDER BY date DESC, time DESC LIMIT 8", conn)
    if not df_recent.empty:
        df_recent['status'] = df_recent['status'].apply(ui_status_from_db)
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
        df_recent['status'] = df_recent['status'].apply(ui_status_from_db)
        st.dataframe(df_recent, use_container_width=True)
    else:
        st.info("No recent tickets added.")

# -----------------------------------------------------------
# View Tickets Page
# -----------------------------------------------------------
def view_tickets_page():
    st.markdown("## 👁️ View Tickets by Status")
    tab1, tab2, tab3 = st.tabs(["📥 Intake", "🔄 Ready to Deliver", "🚚 Delivered"])
    
    with tab1:
        st.subheader("Intake Tickets")
        df_intake = pd.read_sql("SELECT * FROM tickets WHERE status='Intake' ORDER BY date DESC, time DESC", conn)
        if not df_intake.empty:
            df_intake['status'] = df_intake['status'].apply(ui_status_from_db)
            st.dataframe(df_intake, use_container_width=True)
            total_intake = df_intake['num_sub_tickets'].sum()
            total_value = total_intake * st.session_state.ticket_price
            col1, col2 = st.columns(2)
            col1.metric("Total Sub-Tickets", f"{int(total_intake)}")
            col2.metric("Total Value", f"${total_value:,.2f}")
        else:
            st.info("No intake tickets found")
    
    with tab2:
        st.subheader("Ready to Deliver Tickets")
        df_ready = pd.read_sql("SELECT * FROM tickets WHERE status='Return' ORDER BY date DESC, time DESC", conn)
        if not df_ready.empty:
            df_ready['status'] = df_ready['status'].apply(ui_status_from_db)
            st.dataframe(df_ready, use_container_width=True)
            total_ready = df_ready['num_sub_tickets'].sum()
            potential_value = total_ready * st.session_state.ticket_price
            col1, col2 = st.columns(2)
            col1.metric("Total Ready for Delivery", f"{int(total_ready)}")
            col2.metric("Potential Value", f"${potential_value:,.2f}")
        else:
            st.info("No 'Ready to Deliver' tickets found")
    
    with tab3:
        st.subheader("Delivered Tickets")
        df_delivered = pd.read_sql("SELECT * FROM tickets WHERE status='Delivered' ORDER BY date DESC, time DESC", conn)
        if not df_delivered.empty:
            df_delivered['status'] = df_delivered['status'].apply(ui_status_from_db)
            st.dataframe(df_delivered, use_container_width=True)
            total_delivered = df_delivered['num_sub_tickets'].sum()
            earned_value = total_delivered * st.session_state.ticket_price
            col1, col2 = st.columns(2)
            col1.metric("Total Delivered", f"{int(total_delivered)}")
            col2.metric("Earned Value", f"${earned_value:,.2f}")
        else:
            st.info("No delivered tickets found")

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
    # Added an extra tab for SQL Query insert/update
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
                current_status_ui = ui_status_from_db(ticket_data.iloc[0]['status'])
                with st.form("edit_ticket_form"):
                    new_status_ui = st.selectbox("Status", ["Intake", "Ready to Deliver", "Delivered"],
                                                 index=["Intake", "Ready to Deliver", "Delivered"].index(current_status_ui))
                    new_subtickets = st.number_input("Sub-Tickets", min_value=1, value=int(ticket_data.iloc[0]['num_sub_tickets']))
                    new_price = st.number_input("Ticket Price", min_value=0.0, value=float(ticket_data.iloc[0]['pay']), step=0.5)
                    if st.form_submit_button("Update Ticket"):
                        db_status = db_status_from_ui(new_status_ui)
                        cursor.execute("UPDATE tickets SET status = ?, num_sub_tickets = ?, pay = ? WHERE ticket_number = ?",
                                       (db_status, new_subtickets, new_price, ticket_number.strip()))
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
                    new_status_ui = st.selectbox("New Status", ["Intake", "Ready to Deliver", "Delivered"])
                    if st.button("Update Status for All Found Tickets"):
                        db_status = db_status_from_ui(new_status_ui)
                        for t in found_tickets:
                            cursor.execute("UPDATE tickets SET status = ? WHERE ticket_number = ?", (db_status, t))
                        conn.commit()
                        st.success(f"Updated {len(found_tickets)} tickets to {new_status_ui} status")
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
                df_batch['status'] = df_batch['status'].apply(ui_status_from_db)
                st.dataframe(df_batch, use_container_width=True)
                new_status_ui = st.selectbox("New Status for All Tickets in This Batch", ["Intake", "Ready to Deliver", "Delivered"])
                if st.button("Update All Tickets in Batch"):
                    db_status = db_status_from_ui(new_status_ui)
                    cursor.execute("UPDATE tickets SET status = ? WHERE batch_name = ?", (db_status, selected_batch))
                    conn.commit()
                    st.success(f"All tickets in batch '{selected_batch}' updated to '{new_status_ui}'!")
                    df_batch = pd.read_sql("SELECT * FROM tickets WHERE batch_name = ?", conn, params=(selected_batch,))
                    df_batch['status'] = df_batch['status'].apply(ui_status_from_db)
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
# Batches Page (New Page for batch tiles)
# -----------------------------------------------------------
def display_batch_tile(batch_name, total_tickets, status):
    with st.container():
        st.markdown(f"""
        <div style="border: 1px solid #ccc; border-radius: 8px; padding: 15px; margin: 5px; text-align: center;">
          <h4>{batch_name}</h4>
          <p>Total Tickets: {total_tickets}</p>
          <p>Status: {status}</p>
        </div>
        """, unsafe_allow_html=True)
        # "Edit Status" button for the batch tile
        if st.button("Edit Status", key=f"edit_{batch_name}"):
            st.session_state.edit_batch = batch_name

def batch_view_page():
    st.markdown("## 🗂️ Batch View")
    st.write("View batches as tiles by status. Click on 'Edit Status' on any batch to update its status.")
    # Aggregate batches by batch_name
    df_batches = pd.read_sql(
        "SELECT batch_name, SUM(num_sub_tickets) as total_tickets, GROUP_CONCAT(DISTINCT status) as statuses FROM tickets GROUP BY batch_name",
        conn
    )
    # Create four tabs: Intake, Ready to Deliver, Delivered, and All
    tab_intake, tab_ready, tab_delivered, tab_all = st.tabs([
        "Intake Batches", "Ready to Deliver Batches", "Delivered Batches", "All Batches"
    ])
    
    def display_batches(df):
        # Display batches in a grid of 3 columns
        cols = st.columns(3)
        for idx, row in df.iterrows():
            status_str = row["statuses"]
            if "," in status_str:
                display_status = "Mixed"
            else:
                display_status = ui_status_from_db(status_str)
            with cols[idx % 3]:
                display_batch_tile(row["batch_name"], row["total_tickets"], display_status)
    
    with tab_intake:
        df_intake = df_batches[df_batches["statuses"] == "Intake"]
        if not df_intake.empty:
            display_batches(df_intake)
        else:
            st.info("No Intake batches found.")
    
    with tab_ready:
        df_ready = df_batches[df_batches["statuses"] == "Return"]
        if not df_ready.empty:
            display_batches(df_ready)
        else:
            st.info("No Ready to Deliver batches found.")
    
    with tab_delivered:
        df_delivered = df_batches[df_batches["statuses"] == "Delivered"]
        if not df_delivered.empty:
            display_batches(df_delivered)
        else:
            st.info("No Delivered batches found.")
    
    with tab_all:
        if not df_batches.empty:
            display_batches(df_batches)
        else:
            st.info("No batches found.")
    
    # --- Batch Status Update Form ---
    if "edit_batch" in st.session_state and st.session_state.get("edit_batch"):
        st.markdown("## Update Batch Status")
        batch_to_edit = st.session_state.edit_batch
        st.write(f"Updating status for batch: **{batch_to_edit}**")
        # Use a form to update the batch status
        with st.form("update_batch_status_form"):
            new_status_ui = st.selectbox("Select new status", ["Intake", "Ready to Deliver", "Delivered"])
            submitted = st.form_submit_button("Update Batch Status")
            if submitted:
                db_status = db_status_from_ui(new_status_ui)
                cursor.execute("UPDATE tickets SET status = ? WHERE batch_name = ?", (db_status, batch_to_edit))
                conn.commit()
                st.success(f"Batch '{batch_to_edit}' updated to '{new_status_ui}'!")
                st.session_state.edit_batch = None  # Clear the edit flag
                # Optionally, you can force a rerun to update the view:
                # st.experimental_rerun()


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
        st.write("Track and analyze your earnings from delivered tickets")
    
    st.markdown("---")
    col_date1, col_date2 = st.columns(2)
    with col_date1:
        start_date = st.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
    with col_date2:
        end_date = st.date_input("End Date", datetime.date.today())
    
    query = """
        SELECT date,
               SUM(num_sub_tickets * pay) AS day_earnings
        FROM tickets
        WHERE status='Delivered' AND date BETWEEN ? AND ?
        GROUP BY date
        ORDER BY date DESC
    """
    df_income = pd.read_sql(query, conn, params=[start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")])
    if not df_income.empty:
        fig = px.area(df_income, x="date", y="day_earnings", title="Daily Earnings Trend",
                      labels={"day_earnings": "Earnings ($)", "date": "Date"},
                      color_discrete_sequence=["#4CAF50"])
        st.plotly_chart(fig, use_container_width=True)
        st.subheader("Detailed Earnings")
        st.dataframe(df_income, use_container_width=True)
        total_earnings = df_income["day_earnings"].sum()
        st.metric("Total Earnings in Period", f"${total_earnings:,.2f}")
    else:
        st.info("No delivered tickets found in this date range")
    
    st.markdown("---")

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
        "Income": income_page,
        "Batches": batch_view_page,
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
