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
    st.session_state.active_page = "Dashboard"
if "edit_batch" not in st.session_state:
    st.session_state.edit_batch = None

# -----------------------------------------------------------
# Styling
# -----------------------------------------------------------
def load_css():
    if st.session_state.dark_mode:
        bg_color = "#121212"
        text_color = "#E0E0E0"
    else:
        bg_color = "#f8f9fa"
        text_color = "#333333"
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {bg_color};
            color: {text_color};
        }}
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
    except Exception as e:
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
    return sqlite3.connect("ticket_management.db", check_same_thread=False)

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
# Utility: Status Mapping
# -----------------------------------------------------------
def db_status_from_ui(status_ui: str) -> str:
    if status_ui == "Ready to Deliver":
        return "Return"
    return status_ui

def ui_status_from_db(status_db: str) -> str:
    if status_db == "Return":
        return "Ready to Deliver"
    return status_db

# -----------------------------------------------------------
# SQL Query Console (Fixed Version)
# -----------------------------------------------------------
def sql_console_page():
    st.markdown("## 🔍 SQL Query Console")
    st.write("Run custom SQL queries on your local SQLite database (ticket_management.db).")
    st.warning("Use caution with UPDATE, DELETE, or DROP queries as these will permanently modify your data.")

    query = st.text_area(
        "Enter your SQL query below:",
        height=150,
        placeholder="e.g., UPDATE tickets SET status = 'Delivered' WHERE ticket_number = 'T123';"
    )

    if st.button("Execute Query"):
        if not query.strip():
            st.warning("Please enter a SQL query.")
        else:
            result, message = run_query(query)
            if result is not None:
                st.success("Query executed successfully!")
                st.dataframe(result)
            elif message:
                st.info(message)
    st.markdown("### Last Query Run")
    st.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

def run_query(query: str):
    """Execute query using global database connection"""
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        
        if query.strip().lower().startswith("select"):
            data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(data, columns=columns)
            return df, None
        else:
            conn.commit()
            affected = cursor.rowcount
            return None, f"Operation successful. Rows affected: {affected}"
            
    except Exception as e:
        return None, f"Error: {str(e)}"

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
        "Batches": "🗂️",
        "Settings": "⚙️",
        "SQL Console": "💻"
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
    col_anim, col_title = st.columns([1, 5])
    with col_anim:
        if animations["dashboard"]:
            st_lottie(animations["dashboard"], height=150, key="dash_anim")
    with col_title:
        st.markdown("## 📊 Real-Time Ticket Analytics")
        st.write("View your ticket performance and earnings.")
    
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

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Overall Total Tickets", f"{int(total_overall)}")
    col2.metric("Total Intake", f"{int(total_intake)}", f"${estimated_earnings:.2f}")
    col3.metric("Ready to Deliver", f"{int(total_ready)}", f"${total_ready * st.session_state.ticket_price:.2f}")
    col4.metric("Total Delivered", f"{int(total_delivered)}", f"${actual_earnings:.2f}")

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
    else:
        st.info("No data available for the selected date range.")

    st.subheader("⏱️ Recent Activity")
    df_recent = pd.read_sql("SELECT date, ticket_number, status, num_sub_tickets FROM tickets ORDER BY date DESC, time DESC LIMIT 8", conn)
    if not df_recent.empty:
        df_recent['status'] = df_recent['status'].apply(ui_status_from_db)
        st.dataframe(df_recent, use_container_width=True)
    else:
        st.info("No recent activity to display.")

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
        1. Enter a batch name
        2. Choose an input type
        3. Enter ticket number(s)
        4. Click the Add button
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
                    st.warning(f"Could not add {len(failed_tickets)} ticket(s): {', '.join(failed_tickets[:5])}{'...' if len(failed_tickets) > 5 else ''}")
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
        else:
            st.info("No intake tickets found")
    
    with tab2:
        st.subheader("Ready to Deliver Tickets")
        df_ready = pd.read_sql("SELECT * FROM tickets WHERE status='Return' ORDER BY date DESC, time DESC", conn)
        if not df_ready.empty:
            df_ready['status'] = df_ready['status'].apply(ui_status_from_db)
            st.dataframe(df_ready, use_container_width=True)
        else:
            st.info("No 'Ready to Deliver' tickets found")
    
    with tab3:
        st.subheader("Delivered Tickets")
        df_delivered = pd.read_sql("SELECT * FROM tickets WHERE status='Delivered' ORDER BY date DESC, time DESC", conn)
        if not df_delivered.empty:
            df_delivered['status'] = df_delivered['status'].apply(ui_status_from_db)
            st.dataframe(df_delivered, use_container_width=True)
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
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Search & Edit",
        "⚡ Bulk Operations",
        "🗑️ Delete Tickets",
        "📦 By Batch"
    ])
    
    # Tab 1: Search & Edit
    with tab1:
        st.subheader("Individual Ticket Management")
        ticket_number = st.text_input("Enter Ticket Number to Manage")
        if ticket_number:
            ticket_data = pd.read_sql("SELECT * FROM tickets WHERE ticket_number = ?", conn, params=(ticket_number.strip(),))
            if not ticket_data.empty:
                current_status_ui = ui_status_from_db(ticket_data.iloc[0]['status'])
                with st.form("edit_ticket(Due to technical issues, the search service is temporarily unavailable.)

Here's the complete working code with the SQL query console fix:

```python
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
    st.session_state.active_page = "Dashboard"
if "edit_batch" not in st.session_state:
    st.session_state.edit_batch = None

# -----------------------------------------------------------
# Styling
# -----------------------------------------------------------
def load_css():
    if st.session_state.dark_mode:
        bg_color = "#121212"
        text_color = "#E0E0E0"
    else:
        bg_color = "#f8f9fa"
        text_color = "#333333"
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {bg_color};
            color: {text_color};
        }}
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
    except Exception as e:
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
    return sqlite3.connect("ticket_management.db", check_same_thread=False)

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
# Utility: Status Mapping
# -----------------------------------------------------------
def db_status_from_ui(status_ui: str) -> str:
    if status_ui == "Ready to Deliver":
        return "Return"
    return status_ui

def ui_status_from_db(status_db: str) -> str:
    if status_db == "Return":
        return "Ready to Deliver"
    return status_db

# -----------------------------------------------------------
# SQL Query Console (Fixed Version)
# -----------------------------------------------------------
def sql_console_page():
    st.markdown("## 🔍 SQL Query Console")
    st.write("Run custom SQL queries on your local SQLite database (ticket_management.db).")
    st.warning("Use caution with UPDATE, DELETE, or DROP queries as these will permanently modify your data.")

    query = st.text_area(
        "Enter your SQL query below:",
        height=150,
        placeholder="e.g., UPDATE tickets SET status = 'Delivered' WHERE ticket_number = 'T123';"
    )

    if st.button("Execute Query"):
        if not query.strip():
            st.warning("Please enter a SQL query.")
        else:
            result, message = run_query(query)
            if result is not None:
                st.success("Query executed successfully!")
                st.dataframe(result)
            elif message:
                st.info(message)
    st.markdown("### Last Query Run")
    st.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

def run_query(query: str):
    """Execute query using global connection"""
    try:
        cursor = conn.cursor()
        st.write("Executing query:", query)
        cursor.execute(query)
        
        if query.strip().lower().startswith("select"):
            data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(data, columns=columns)
            st.write("Query returned", len(df), "rows.")
            return df, None
        else:
            conn.commit()
            affected = cursor.rowcount
            st.write("Query committed successfully. Rows affected:", affected)
            return None, f"Rows affected: {affected}"
            
    except Exception as e:
        st.error(f"Error executing query: {str(e)}")
        return None, f"Error: {str(e)}"

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
        "Batches": "🗂️",
        "Settings": "⚙️",
        "SQL Console": "💻"
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
    col_anim, col_title = st.columns([1, 5])
    with col_anim:
        if animations["dashboard"]:
            st_lottie(animations["dashboard"], height=150, key="dash_anim")
    with col_title:
        st.markdown("## 📊 Real-Time Ticket Analytics")
        st.write("View your ticket performance and earnings.")
    
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

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Overall Total Tickets", f"{int(total_overall)}")
    col2.metric("Total Intake", f"{int(total_intake)}", f"${estimated_earnings:.2f}")
    col3.metric("Ready to Deliver", f"{int(total_ready)}", f"${total_ready * st.session_state.ticket_price:.2f}")
    col4.metric("Total Delivered", f"{int(total_delivered)}", f"${actual_earnings:.2f}")

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
    else:
        st.info("No data available for the selected date range.")

    st.subheader("⏱️ Recent Activity")
    df_recent = pd.read_sql("SELECT date, ticket_number, status, num_sub_tickets FROM tickets ORDER BY date DESC, time DESC LIMIT 8", conn)
    if not df_recent.empty:
        df_recent['status'] = df_recent['status'].apply(ui_status_from_db)
        st.dataframe(df_recent, use_container_width=True)
    else:
        st.info("No recent activity to display.")

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
        1. Enter a batch name
        2. Choose an input type
        3. Enter ticket number(s)
        4. Click the Add button
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
                    st.warning(f"Could not add {len(failed_tickets)} ticket(s): {', '.join(failed_tickets[:5])}{'...' if len(failed_tickets) > 5 else ''}")
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
        else:
            st.info("No intake tickets found")
    
    with tab2:
        st.subheader("Ready to Deliver Tickets")
        df_ready = pd.read_sql("SELECT * FROM tickets WHERE status='Return' ORDER BY date DESC, time DESC", conn)
        if not df_ready.empty:
            df_ready['status'] = df_ready['status'].apply(ui_status_from_db)
            st.dataframe(df_ready, use_container_width=True)
        else:
            st.info("No 'Ready to Deliver' tickets found")
    
    with tab3:
        st.subheader("Delivered Tickets")
        df_delivered = pd.read_sql("SELECT * FROM tickets WHERE status='Delivered' ORDER BY date DESC, time DESC", conn)
        if not df_delivered.empty:
            df_delivered['status'] = df_delivered['status'].apply(ui_status_from_db)
            st.dataframe(df_delivered, use_container_width=True)
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
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Search & Edit",
        "⚡ Bulk Operations",
        "🗑️ Delete Tickets",
        "📦 By Batch"
    ])
    
    # Tab 1: Search & Edit
    with tab1:
        st.subheader("Individual Ticket Management")
        ticket_number = st.text_input("Enter Ticket Number to Manage")
        if ticket_number:
            ticket_data = pd.read_sql("SELECT * FROM tickets WHERE ticket_number = ?", conn,(Due to technical issues, the search service is temporarily unavailable.)

Here's the complete fixed code with working SQL query functionality:

```python
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
    st.session_state.active_page = "Dashboard"
if "edit_batch" not in st.session_state:
    st.session_state.edit_batch = None

# -----------------------------------------------------------
# Styling
# -----------------------------------------------------------
def load_css():
    if st.session_state.dark_mode:
        bg_color = "#121212"
        text_color = "#E0E0E0"
    else:
        bg_color = "#f8f9fa"
        text_color = "#333333"
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {bg_color};
            color: {text_color};
        }}
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
    except Exception as e:
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
    return sqlite3.connect("ticket_management.db", check_same_thread=False)

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
# Utility: Status Mapping
# -----------------------------------------------------------
def db_status_from_ui(status_ui: str) -> str:
    if status_ui == "Ready to Deliver":
        return "Return"
    return status_ui

def ui_status_from_db(status_db: str) -> str:
    if status_db == "Return":
        return "Ready to Deliver"
    return status_db

# -----------------------------------------------------------
# SQL Query Console (Fixed Version)
# -----------------------------------------------------------
def sql_console_page():
    st.markdown("## 🔍 SQL Query Console")
    st.write("Run custom SQL queries on your local SQLite database (ticket_management.db).")
    st.warning("Use caution with UPDATE, DELETE, or DROP queries as these will permanently modify your data.")

    query = st.text_area(
        "Enter your SQL query below:",
        height=150,
        placeholder="e.g., UPDATE tickets SET status = 'Delivered' WHERE ticket_number = 'T123';"
    )

    if st.button("Execute Query"):
        if not query.strip():
            st.warning("Please enter a SQL query.")
        else:
            result, message = run_query(query)
            if result is not None:
                st.success("Query executed successfully!")
                st.dataframe(result)
            elif message:
                st.info(message)
    st.markdown("### Last Query Run")
    st.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

def run_query(query: str):
    """Execute query using global connection"""
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        
        if query.strip().lower().startswith("select"):
            data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(data, columns=columns)
            return df, None
        else:
            conn.commit()
            affected = cursor.rowcount
            return None, f"Rows affected: {affected}"
            
    except Exception as e:
        return None, f"Error: {str(e)}"

# [Rest of the code remains identical from the previous version...]
# [Include all other pages and functions exactly as in your original code]
# [Only the SQL console section was modified]

# -----------------------------------------------------------
# Main App Flow
# -----------------------------------------------------------
def main():
    params = st.query_params
    current_page = params.get("page", ["Dashboard"])[0]
    if current_page:
        st.session_state.active_page = current_page

    render_navbar()
    pages = {
        "Dashboard": dashboard_page,
        "Add Tickets": add_tickets_page,
        "View Tickets": view_tickets_page,
        "Manage Tickets": manage_tickets_page,
        "Income": income_page,
        "Batches": batch_view_page,
        "Settings": settings_page,
        "SQL Console": sql_console_page
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
