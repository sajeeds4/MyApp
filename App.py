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
# Styling
# -----------------------------------------------------------
def load_css():
    if st.session_state.dark_mode:
        primary_color = "#1E88E5"
        bg_color = "#121212"
        card_bg = "#1E1E1E"
        text_color = "#E0E0E0"
        subtext_color = "#AAAAAA"
    else:
        primary_color = "#4CAF50"
        bg_color = "#f8f9fa"
        card_bg = "#ffffff"
        text_color = "#333333"
        subtext_color = "#666666"
    
    st.markdown(
        f"""
        <style>
        /* Global Styles */
        .stApp {{
            background-color: {bg_color};
            color: {text_color};
        }}
        
        /* Top Navigation */
        .top-nav {{
            background-color: {card_bg};
            padding: 12px 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .nav-buttons {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        
        .nav-btn {{
            background-color: {primary_color};
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 6px;
            cursor: pointer;
            transition: transform 0.3s ease;
        }}
        
        .nav-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }}
        
        /* Metrics */
        .metric-row {{
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        
        .metric-card {{
            background: {card_bg};
            border-radius: 10px;
            padding: 20px;
            flex: 1;
            min-width: 220px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border-left: 4px solid {primary_color};
            transition: transform 0.3s ease;
        }}
        
        .metric-card:hover {{
            transform: translateY(-5px);
        }}
        
        .metric-title {{
            font-size: 16px;
            color: {subtext_color};
            margin-bottom: 8px;
        }}
        
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: {text_color};
        }}
        
        .metric-subvalue {{
            font-size: 16px;
            color: {primary_color};
        }}
        
        /* Page Containers */
        .content-container {{
            background: {card_bg};
            border-radius: 10px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            animation: fadeIn 0.5s ease-in-out;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        /* Custom Footer */
        .footer {{
            text-align: center;
            padding: 15px;
            font-size: 0.8rem;
            color: {subtext_color};
            border-top: 1px solid rgba(0,0,0,0.1);
            margin-top: 30px;
        }}
        
        /* Data Table Styling */
        .dataframe {{
            border-collapse: collapse;
            width: 100%;
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .dataframe th {{
            background-color: rgba(76, 175, 80, 0.2);
            padding: 12px 15px;
            text-align: left;
        }}
        
        .dataframe td {{
            padding: 10px 15px;
            border-bottom: 1px solid rgba(0,0,0,0.05);
        }}
        
        .dataframe tr:hover {{
            background-color: rgba(0,0,0,0.03);
        }}
        
        /* Input Fields */
        .stTextInput input, .stNumberInput input, .stDateInput input {{
            border-radius: 6px;
            border: 1px solid #ccc;
            padding: 8px 12px;
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
    # Create tickets table if not exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        time TEXT,
        batch_name TEXT,
        ticket_number TEXT UNIQUE,
        num_sub_tickets INTEGER DEFAULT 1,
        -- "Return" means "ready to deliver" in the DB,
        -- but we display "Ready to Deliver" in the UI.
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
# Utility: UI ↔ DB Status Mapping
# -----------------------------------------------------------
# We use this helper so the UI can show "Ready to Deliver" but store "Return" in the database.
def db_status_from_ui(status_ui: str) -> str:
    """Convert the user-facing status label to the DB status."""
    if status_ui == "Ready to Deliver":
        return "Return"
    return status_ui  # 'Intake' or 'Delivered'

def ui_status_from_db(status_db: str) -> str:
    """Convert the DB status to the user-facing label."""
    if status_db == "Return":
        return "Ready to Deliver"
    return status_db

# -----------------------------------------------------------
# Navigation
# -----------------------------------------------------------
def render_navbar():
    pages = {
        "Dashboard": "📊",
        "Add Tickets": "➕",
        "View Tickets": "👁️",
        "Manage Tickets": "🔄",
        "Income": "💰",
        "Settings": "⚙️"
    }
    
    st.markdown(f"""
    <div class="top-nav">
        <h2>🎟️ {st.session_state.company_name} Ticket System</h2>
        <div class="nav-buttons">
    """, unsafe_allow_html=True)
    
    cols = st.columns(len(pages))
    for i, (page, icon) in enumerate(pages.items()):
        if cols[i].button(f"{icon} {page}"):
            st.session_state.active_page = page
    st.markdown("</div></div>", unsafe_allow_html=True)

# -----------------------------------------------------------
# Page: Dashboard
# -----------------------------------------------------------
def dashboard_page():
    col_anim1, col_anim2 = st.columns([1, 5])
    with col_anim1:
        if animations["dashboard"]:
            st_lottie(animations["dashboard"], height=150, key="dash_anim")
    with col_anim2:
        st.markdown("## 📊 Real-Time Ticket Analytics")
        st.write("View and analyze your ticket performance and earnings at a glance.")
    
    # Pull counts directly from DB statuses
    cursor.execute("SELECT SUM(num_sub_tickets) FROM tickets WHERE status='Intake'")
    total_intake = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(num_sub_tickets) FROM tickets WHERE status='Return'")
    total_returned = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(num_sub_tickets) FROM tickets WHERE status='Delivered'")
    total_delivered = cursor.fetchone()[0] or 0
    
    estimated_earnings = total_intake * st.session_state.ticket_price
    actual_earnings = total_delivered * st.session_state.ticket_price
    
    # Show metrics, rename "Return" → "Ready to Deliver", remove minus sign
    st.markdown(
        f"""
        <div class="metric-row">
            <div class="metric-card">
                <div class="metric-title">📥 Total Intake</div>
                <div class="metric-value">{int(total_intake)}</div>
                <div class="metric-subvalue">${estimated_earnings:.2f}</div>
            </div>
            
            <div class="metric-card" style="border-color: #FF9800;">
                <div class="metric-title">🔄 Ready to Deliver</div>
                <div class="metric-value">{int(total_returned)}</div>
                <div class="metric-subvalue" style="color: #FF9800;">${total_returned * st.session_state.ticket_price:.2f}</div>
            </div>
            
            <div class="metric-card" style="border-color: #2196F3;">
                <div class="metric-title">🚚 Total Delivered</div>
                <div class="metric-value">{int(total_delivered)}</div>
                <div class="metric-subvalue" style="color: #2196F3;">${actual_earnings:.2f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True
    )
    
    st.markdown('<div class="content-container">', unsafe_allow_html=True)
    st.subheader("📅 Date Range Analysis")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", datetime.date.today())
    
    query = """
    SELECT date, 
           SUM(CASE WHEN status='Delivered' THEN num_sub_tickets ELSE 0 END) as delivered,
           SUM(CASE WHEN status='Return' THEN num_sub_tickets ELSE 0 END) as returned,
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
        fig.add_trace(go.Scatter(
            x=df_daily['date'], 
            y=df_daily['delivered'],
            mode='lines+markers',
            name='Delivered',
            line=dict(color='#2196F3', width=3),
            fill='tozeroy',
            marker=dict(size=8)
        ))
        fig.add_trace(go.Scatter(
            x=df_daily['date'], 
            y=df_daily['returned'],
            mode='lines+markers',
            name='Ready to Deliver',  # Renamed in UI
            line=dict(color='#FF9800', width=3),
            marker=dict(size=8)
        ))
        fig.add_trace(go.Scatter(
            x=df_daily['date'], 
            y=df_daily['intake'],
            mode='lines+markers',
            name='Intake',
            line=dict(color='#4CAF50', width=3, dash='dot'),
            marker=dict(size=8)
        ))
        fig.update_layout(
            title='Daily Ticket Activity',
            xaxis_title='Date',
            yaxis_title='Number of Tickets',
            legend_title='Status',
            height=500,
            template='plotly_white',
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        df_daily['delivered_value'] = df_daily['delivered'] * st.session_state.ticket_price
        fig2 = px.bar(
            df_daily, 
            x='date', 
            y='delivered_value',
            title="Daily Delivery Earnings",
            labels={'delivered_value': 'Earnings ($)', 'date': 'Date'},
            color_discrete_sequence=['#4CAF50']
        )
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No data available for selected date range")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="content-container">', unsafe_allow_html=True)
    st.subheader("📈 Performance Statistics")
    
    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        total_intake = max(total_intake, 0)
        conversion_rate = (total_delivered / total_intake * 100) if total_intake > 0 else 0
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=conversion_rate,
            title={'text': "Delivery Rate"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#4CAF50"},
                'steps': [
                    {'range': [0, 33], 'color': "#FFCDD2"},
                    {'range': [33, 66], 'color': "#FFECB3"},
                    {'range': [66, 100], 'color': "#C8E6C9"}
                ]
            }
        ))
        fig_gauge.update_layout(height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    with col_stat2:
        query_status = "SELECT status, COUNT(*) as count FROM tickets GROUP BY status"
        df_status = pd.read_sql(query_status, conn)
        if not df_status.empty:
            # Convert DB statuses to UI labels
            df_status['status_ui'] = df_status['status'].apply(ui_status_from_db)
            fig_pie = px.pie(
                df_status, 
                values='count', 
                names='status_ui',
                title="Ticket Status Distribution",
                color='status_ui',
                color_discrete_map={
                    'Intake': '#4CAF50',
                    'Ready to Deliver': '#FF9800',
                    'Delivered': '#2196F3'
                }
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(height=300)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No status data available")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="content-container">', unsafe_allow_html=True)
    st.subheader("⏱️ Recent Activity")
    df_recent = pd.read_sql("SELECT date, ticket_number, status, num_sub_tickets FROM tickets ORDER BY date DESC, time DESC LIMIT 8", conn)
    if not df_recent.empty:
        # Convert DB status to UI
        df_recent['status'] = df_recent['status'].apply(ui_status_from_db)
        st.dataframe(df_recent, use_container_width=True)
    else:
        st.info("No recent activity to display")
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------
# Page: Add Tickets
# -----------------------------------------------------------
def add_tickets_page():
    col_anim, col_title = st.columns([1, 5])
    with col_anim:
        if animations["tickets"]:
            st_lottie(animations["tickets"], height=150, key="ticket_anim")
    with col_title:
        st.markdown("## ➕ Add New Tickets")
        st.write(f"Current ticket price: ${st.session_state.ticket_price:.2f} per sub-ticket")
    
    st.markdown('<div class="content-container">', unsafe_allow_html=True)
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
        ### Quick Instructions
        1. Enter batch name (optional)
        2. Choose input type
        3. Enter ticket number(s)
        4. Click Add button
        """)
    
    if ticket_input_type == "Multiple/General":
        tickets_text = st.text_area("Enter Ticket Number(s)", placeholder="Space or new-line separated ticket numbers")
        col_submit1, col_submit2 = st.columns([1, 5])
        with col_submit1:
            submit_button = st.button("Add Tickets", use_container_width=True)
        if submit_button:
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
                    st.warning(
                        f"Could not add {len(failed_tickets)} ticket(s) because they already exist: "
                        f"{', '.join(failed_tickets[:5])}{'...' if len(failed_tickets) > 5 else ''}"
                    )
            else:
                st.warning("Please enter ticket number(s).")
    else:
        col_large1, col_large2 = st.columns(2)
        with col_large1:
            large_ticket = st.text_input("Large Ticket Number", placeholder="Enter the main ticket number")
        with col_large2:
            sub_count = st.number_input("Number of Sub-Tickets", min_value=1, value=5, step=1)
        col_submit1, col_submit2 = st.columns([1, 5])
        with col_submit1:
            submit_large = st.button("Add Large Ticket", use_container_width=True)
        if submit_large:
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
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="content-container">', unsafe_allow_html=True)
    st.subheader("Recent Additions")
    df_recent = pd.read_sql("SELECT date, time, batch_name, ticket_number, num_sub_tickets, status FROM tickets ORDER BY id DESC LIMIT 5", conn)
    if not df_recent.empty:
        # Convert DB statuses to UI
        df_recent['status'] = df_recent['status'].apply(ui_status_from_db)
        st.dataframe(df_recent, use_container_width=True)
    else:
        st.info("No recent tickets added.")
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------
# Page: View Tickets
# -----------------------------------------------------------
def view_tickets_page():
    st.markdown("## 👁️ View Tickets by Status")
    # Renamed second tab from 'Return' → 'Ready to Deliver'
    tab1, tab2, tab3 = st.tabs(["📥 Intake", "🔄 Ready to Deliver", "🚚 Delivered"])
    
    # Intake tab
    with tab1:
        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        df_intake = pd.read_sql("SELECT * FROM tickets WHERE status='Intake' ORDER BY date DESC, time DESC", conn)
        if not df_intake.empty:
            df_intake['status'] = df_intake['status'].apply(ui_status_from_db)
            st.dataframe(df_intake, use_container_width=True)
            total_intake = df_intake['num_sub_tickets'].sum()
            total_value = total_intake * st.session_state.ticket_price
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Sub-Tickets", f"{int(total_intake)}")
            with col2:
                st.metric("Total Value", f"${total_value:,.2f}")
        else:
            st.info("No intake tickets found")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Ready to Deliver tab (DB status='Return')
    with tab2:
        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        df_return = pd.read_sql("SELECT * FROM tickets WHERE status='Return' ORDER BY date DESC, time DESC", conn)
        if not df_return.empty:
            # Convert DB statuses to UI
            df_return['status'] = df_return['status'].apply(ui_status_from_db)
            st.dataframe(df_return, use_container_width=True)
            total_return = df_return['num_sub_tickets'].sum()
            potential_value = total_return * st.session_state.ticket_price
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Ready for Delivery", f"{int(total_return)}")
            with col2:
                st.metric("Potential Value", f"${potential_value:,.2f}")
        else:
            st.info("No 'Ready to Deliver' tickets found")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Delivered tab
    with tab3:
        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        df_delivered = pd.read_sql("SELECT * FROM tickets WHERE status='Delivered' ORDER BY date DESC, time DESC", conn)
        if not df_delivered.empty:
            df_delivered['status'] = df_delivered['status'].apply(ui_status_from_db)
            st.dataframe(df_delivered, use_container_width=True)
            total_delivered = df_delivered['num_sub_tickets'].sum()
            earned_value = total_delivered * st.session_state.ticket_price
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Delivered", f"{int(total_delivered)}")
            with col2:
                st.metric("Earned Value", f"${earned_value:,.2f}")
        else:
            st.info("No delivered tickets found")
        st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------
# Page: Manage Tickets
# -----------------------------------------------------------
def manage_tickets_page():
    col_anim, col_title = st.columns([1, 5])
    with col_anim:
        if animations["settings"]:
            st_lottie(animations["settings"], height=150, key="manage_anim")
    with col_title:
        st.markdown("## 🔄 Manage Tickets")
        st.write("Advanced ticket management operations")
    
    st.markdown('<div class="content-container">', unsafe_allow_html=True)
    # Added a 4th tab "By Batch"
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Search & Edit",
        "⚡ Bulk Operations",
        "🗑️ Delete Tickets",
        "📦 By Batch"
    ])
    
    # ---- Tab 1: Search & Edit ----
    with tab1:
        st.subheader("Individual Ticket Management")
        ticket_number = st.text_input("Enter Ticket Number to Manage")
        if ticket_number:
            ticket_data = pd.read_sql("SELECT * FROM tickets WHERE ticket_number = ?", conn, params=(ticket_number.strip(),))
            if not ticket_data.empty:
                # Convert DB status → UI label
                current_status_ui = ui_status_from_db(ticket_data.iloc[0]['status'])
                with st.form("edit_ticket_form"):
                    new_status_ui = st.selectbox(
                        "Status",
                        ["Intake", "Ready to Deliver", "Delivered"],
                        index=["Intake", "Ready to Deliver", "Delivered"].index(current_status_ui)
                    )
                    new_subtickets = st.number_input(
                        "Sub-Tickets",
                        min_value=1,
                        value=int(ticket_data.iloc[0]['num_sub_tickets'])
                    )
                    new_price = st.number_input(
                        "Ticket Price",
                        min_value=0.0,
                        value=float(ticket_data.iloc[0]['pay']),
                        step=0.5
                    )
                    if st.form_submit_button("Update Ticket"):
                        # Convert UI status back to DB
                        db_status = db_status_from_ui(new_status_ui)
                        cursor.execute(
                            "UPDATE tickets SET status = ?, num_sub_tickets = ?, pay = ? WHERE ticket_number = ?",
                            (db_status, new_subtickets, new_price, ticket_number.strip())
                        )
                        conn.commit()
                        st.success("Ticket updated successfully!")
                        if animations["success"]:
                            st_lottie(animations["success"], height=80)
            else:
                st.warning("Ticket not found in database")
    
    # ---- Tab 2: Bulk Operations ----
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
                st.warning(
                    f"{len(missing_tickets)} tickets not found: "
                    f"{', '.join(missing_tickets[:3])}{'...' if len(missing_tickets) > 3 else ''}"
                )
            if found_tickets:
                st.success(f"{len(found_tickets)} valid tickets found")
                if bulk_action == "Update Status":
                    # Let the user pick the UI status label
                    new_status_ui = st.selectbox("New Status", ["Intake", "Ready to Deliver", "Delivered"])
                    if st.button("Update Status for All Found Tickets"):
                        db_status = db_status_from_ui(new_status_ui)
                        for t in found_tickets:
                            cursor.execute(
                                "UPDATE tickets SET status = ? WHERE ticket_number = ?",
                                (db_status, t)
                            )
                        conn.commit()
                        st.success(f"Updated {len(found_tickets)} tickets to {new_status_ui} status")
                elif bulk_action == "Change Price":
                    new_price = st.number_input("New Price", min_value=0.0, value=st.session_state.ticket_price)
                    if st.button("Update Price for All Found Tickets"):
                        for t in found_tickets:
                            cursor.execute(
                                "UPDATE tickets SET pay = ? WHERE ticket_number = ?",
                                (new_price, t)
                            )
                        conn.commit()
                        st.success(f"Updated pricing for {len(found_tickets)} tickets")
                elif bulk_action == "Add Subtickets":
                    add_count = st.number_input("Additional Subtickets", min_value=1, value=1)
                    if st.button("Add Subtickets to All Found Tickets"):
                        for t in found_tickets:
                            cursor.execute(
                                "UPDATE tickets SET num_sub_tickets = num_sub_tickets + ? WHERE ticket_number = ?",
                                (add_count, t)
                            )
                        conn.commit()
                        st.success(f"Added {add_count} subtickets to {len(found_tickets)} tickets")
    
    # ---- Tab 3: Delete Tickets ----
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
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date")
            with col2:
                end_date = st.date_input("End Date")
            if st.button("Delete Tickets in Date Range"):
                cursor.execute(
                    "DELETE FROM tickets WHERE date BETWEEN ? AND ?",
                    (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
                )
                conn.commit()
                st.success(f"Deleted {cursor.rowcount} tickets from {start_date} to {end_date}")
    
    # ---- Tab 4: By Batch ----
    with tab4:
        st.subheader("Manage Tickets By Batch Name")
        # 1. Fetch all distinct batch names
        cursor.execute("SELECT DISTINCT batch_name FROM tickets")
        batch_rows = cursor.fetchall()
        batch_names = [row[0] for row in batch_rows if row[0]]
        
        if batch_names:
            selected_batch = st.selectbox("Select a Batch to Manage", batch_names)
            
            if selected_batch:
                # Show all tickets in this batch
                df_batch = pd.read_sql(
                    "SELECT * FROM tickets WHERE batch_name = ?",
                    conn,
                    params=(selected_batch,)
                )
                # Convert DB status to UI
                df_batch['status'] = df_batch['status'].apply(ui_status_from_db)
                st.dataframe(df_batch, use_container_width=True)
                
                # Let user pick a new status (UI label)
                new_status_ui = st.selectbox(
                    "New Status for All Tickets in This Batch",
                    ["Intake", "Ready to Deliver", "Delivered"]
                )
                
                if st.button("Update All Tickets in Batch"):
                    # Convert UI label → DB status
                    db_status = db_status_from_ui(new_status_ui)
                    cursor.execute(
                        "UPDATE tickets SET status = ? WHERE batch_name = ?",
                        (db_status, selected_batch)
                    )
                    conn.commit()
                    st.success(
                        f"All tickets in batch '{selected_batch}' updated to '{new_status_ui}'!"
                    )
                    # Re-display updated dataframe
                    df_batch = pd.read_sql(
                        "SELECT * FROM tickets WHERE batch_name = ?",
                        conn,
                        params=(selected_batch,)
                    )
                    df_batch['status'] = df_batch['status'].apply(ui_status_from_db)
                    st.dataframe(df_batch, use_container_width=True)
        else:
            st.info("No batches found in the database.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------
# Page: Income
# -----------------------------------------------------------
def income_page():
    col_anim, col_title = st.columns([1, 5])
    with col_anim:
        if animations["money"]:
            st_lottie(animations["money"], height=150, key="money_anim")
    with col_title:
        st.markdown("## 💰 Income Analysis")
        st.write("Track and analyze your earnings from delivered tickets")
    
    st.markdown('<div class="content-container">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
    with col2:
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
        fig = px.area(
            df_income,
            x="date",
            y="day_earnings",
            title="Daily Earnings Trend",
            labels={"day_earnings": "Earnings ($)", "date": "Date"},
            color_discrete_sequence=["#4CAF50"]
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Detailed Earnings")
        st.dataframe(df_income, use_container_width=True)
        
        total_earnings = df_income["day_earnings"].sum()
        st.metric("Total Earnings in Period", f"${total_earnings:,.2f}")
    else:
        st.info("No delivered tickets found in this date range")
    
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------
# Page: Settings
# -----------------------------------------------------------
def settings_page():
    col_anim, col_title = st.columns([1, 5])
    with col_anim:
        if animations["settings"]:
            st_lottie(animations["settings"], height=150, key="settings_anim")
    with col_title:
        st.markdown("## ⚙️ System Settings")
        st.write("Configure application preferences and defaults")
    
    st.markdown('<div class="content-container">', unsafe_allow_html=True)
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
            # st.experimental_rerun()  # Not strictly needed; checkbox triggers a rerun
        st.color_picker("Primary Color", value="#4CAF50", key="primary_color")
    
    st.markdown('</div>', unsafe_allow_html=True)

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
        "Settings": settings_page
    }
    
    active_page = st.session_state.active_page
    if active_page in pages:
        pages[active_page]()
    
    st.markdown(
        f"""
        <div class="footer">
            <p>{st.session_state.company_name} Ticket System • {datetime.datetime.now().year}</p>
            <p>Powered by Streamlit • v1.0</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
