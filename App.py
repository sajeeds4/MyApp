import streamlit as st
import pandas as pd
import datetime
import requests
from streamlit_lottie import st_lottie
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import numpy as np
import streamlit.components.v1 as components

# MongoDB imports
import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

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
AVAILABLE_STATUSES = [
    "Intake",
    "Return",     # previously "Ready to Deliver"
    "Delivered",
    "On Hold",
    "Cancelled"
]

STATUS_LABELS = {
    "Intake": "Intake",
    "Return": "Ready to Deliver",
    "Delivered": "Delivered",
    "On Hold": "On Hold",
    "Cancelled": "Cancelled"
}

def display_status(status_in_db: str) -> str:
    return STATUS_LABELS.get(status_in_db, status_in_db)

def get_db_status_from_display(ui_label: str) -> str:
    for db_val, label in STATUS_LABELS.items():
        if label == ui_label:
            return db_val
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
# Styling (Basic CSS)
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
# MongoDB Setup
# -----------------------------------------------------------
def get_mongo_collection():
    # Replace <username> and <password> with your actual credentials
    uri = "mongodb+srv://<username>:<password>@cluster0.ygnrrkc.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client["ticket_management"]  # Use any DB name you want
    tickets_coll = db["tickets"]

    # Create a unique index on ticket_number so duplicates are rejected
    # This runs every time but only really creates once.
    tickets_coll.create_index(
        [("ticket_number", pymongo.ASCENDING)], 
        unique=True
    )

    return tickets_coll

tickets_collection = get_mongo_collection()

# -----------------------------------------------------------
# Navigation
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
# Helper: Summation by Status
# -----------------------------------------------------------
def get_total_subtickets_by_status(status_name):
    """
    Equivalent to SELECT SUM(num_sub_tickets) WHERE status = ?
    """
    pipeline = [
        {"$match": {"status": status_name}},
        {"$group": {"_id": None, "total": {"$sum": "$num_sub_tickets"}}}
    ]
    result = list(tickets_collection.aggregate(pipeline))
    return result[0]["total"] if result else 0

def get_total_subtickets_all():
    """
    Equivalent to SELECT SUM(num_sub_tickets) FROM tickets
    """
    pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$num_sub_tickets"}}}
    ]
    result = list(tickets_collection.aggregate(pipeline))
    return result[0]["total"] if result else 0

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

    total_intake = get_total_subtickets_by_status("Intake")
    total_ready = get_total_subtickets_by_status("Return")  # "Ready to Deliver"
    total_delivered = get_total_subtickets_by_status("Delivered")
    total_overall = get_total_subtickets_all()

    estimated_earnings = total_intake * st.session_state.ticket_price
    actual_earnings = total_delivered * st.session_state.ticket_price

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

    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    # Aggregation to mimic: date, sum delivered, sum ready, sum intake
    pipeline = [
        {"$match": {"date": {"$gte": start_str, "$lte": end_str}}},
        {"$group": {
            "_id": "$date",
            "delivered": {
                "$sum": {
                    "$cond": [{"$eq": ["$status", "Delivered"]}, "$num_sub_tickets", 0]
                }
            },
            "ready": {
                "$sum": {
                    "$cond": [{"$eq": ["$status", "Return"]}, "$num_sub_tickets", 0]
                }
            },
            "intake": {
                "$sum": {
                    "$cond": [{"$eq": ["$status", "Intake"]}, "$num_sub_tickets", 0]
                }
            }
        }},
        {"$sort": {"_id": 1}}
    ]
    result = list(tickets_collection.aggregate(pipeline))
    df_daily = pd.DataFrame(result)
    if not df_daily.empty:
        df_daily.rename(columns={"_id": "date"}, inplace=True)
        # Convert date from string to datetime for better plotting
        df_daily["date"] = pd.to_datetime(df_daily["date"], format="%Y-%m-%d", errors="coerce")

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

        # Another chart for daily delivery earnings
        df_daily['delivered_value'] = df_daily['delivered'] * st.session_state.ticket_price
        fig2 = px.bar(df_daily, x='date', y='delivered_value',
                      title="Daily Delivery Earnings",
                      labels={'delivered_value': 'Earnings ($)', 'date': 'Date'})
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No data available for selected date range")

    # Performance Statistics
    st.subheader("📈 Performance Statistics")
    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        total_intake_safe = max(total_intake, 0)
        conversion_rate = (total_delivered / total_intake_safe * 100) if total_intake_safe > 0 else 0
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
        # Query status distribution: SELECT status, COUNT(*) from tickets GROUP BY status
        pipeline_status = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        result_status = list(tickets_collection.aggregate(pipeline_status))
        df_status = pd.DataFrame(result_status)
        if not df_status.empty:
            df_status.rename(columns={"_id": "status"}, inplace=True)
            # Convert to UI label
            df_status['status_ui'] = df_status['status'].apply(display_status)
            fig_pie = px.pie(df_status, values='count', names='status_ui',
                             title="Ticket Status Distribution")
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(height=300)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No status data available")

    # Recent Activity
    st.subheader("⏱️ Recent Activity")
    # SELECT date, ticket_number, status, num_sub_tickets FROM tickets ORDER BY date DESC, time DESC LIMIT 8
    # We'll sort by date+time descending (using insertion order for fallback)
    docs = tickets_collection.find({}, {
        "_id": 0,
        "date": 1,
        "ticket_number": 1,
        "status": 1,
        "num_sub_tickets": 1,
        "time": 1
    }).sort([("date", -1), ("time", -1)]).limit(8)

    df_recent = pd.DataFrame(list(docs))
    if not df_recent.empty:
        df_recent["status"] = df_recent["status"].apply(display_status)
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
            # We'll generate a batch name automatically
            # But in MongoDB, let's just do a quick distinct count
            existing_batches = tickets_collection.distinct("batch_name")
            batch_count = len(existing_batches) + 1
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
                        doc = {
                            "date": current_date,
                            "time": current_time,
                            "batch_name": batch_name,
                            "ticket_number": t,
                            "num_sub_tickets": 1,
                            "status": "Intake",
                            "pay": st.session_state.ticket_price,
                            "comments": "",
                            "ticket_day": "",
                            "ticket_school": ""
                        }
                        try:
                            tickets_collection.insert_one(doc)
                            success_count += 1
                        except pymongo.errors.DuplicateKeyError:
                            failed_tickets.append(t)
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
        if st.button("Add Large Ticket"):
            if large_ticket.strip():
                doc = {
                    "date": current_date,
                    "time": current_time,
                    "batch_name": batch_name,
                    "ticket_number": large_ticket.strip(),
                    "num_sub_tickets": sub_count,
                    "status": "Intake",
                    "pay": st.session_state.ticket_price,
                    "comments": "",
                    "ticket_day": "",
                    "ticket_school": ""
                }
                try:
                    tickets_collection.insert_one(doc)
                    st.success(f"Added large ticket '{large_ticket}' with {sub_count} sub-tickets to batch '{batch_name}'.")
                    if animations["success"]:
                        st_lottie(animations["success"], height=120)
                except pymongo.errors.DuplicateKeyError:
                    st.error(f"Ticket '{large_ticket.strip()}' already exists.")
            else:
                st.warning("Please enter a valid ticket number.")

    # Recent additions
    st.markdown("---")
    st.subheader("Recent Additions")
    recent_docs = tickets_collection.find({}).sort([("_id", -1)]).limit(5)
    df_recent = pd.DataFrame(list(recent_docs))
    if not df_recent.empty:
        df_recent['status'] = df_recent['status'].apply(display_status)
        # Hide _id if you want
        if "_id" in df_recent.columns:
            df_recent.drop(columns=["_id"], inplace=True)
        st.dataframe(df_recent, use_container_width=True)
    else:
        st.info("No recent tickets added.")

# -----------------------------------------------------------
# View Tickets Page
# -----------------------------------------------------------
def view_tickets_page():
    st.markdown("## 👁️ View Tickets by Status")
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📥 Intake",
        "🔄 Ready to Deliver",
        "🚚 Delivered",
        "On Hold",
        "Cancelled"
    ])

    def show_status_data(status_key, container):
        with container:
            st.subheader(f"Tickets with status '{display_status(status_key)}'")
            docs = tickets_collection.find({"status": status_key}).sort([("_id", -1)])
            df_data = pd.DataFrame(list(docs))
            if not df_data.empty:
                df_data['status'] = df_data['status'].apply(display_status)
                if "_id" in df_data.columns:
                    df_data.drop(columns=["_id"], inplace=True)
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
    # Ready
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

    # Tab 1: Search & Edit
    with tab1:
        st.subheader("Individual Ticket Management")
        ticket_number = st.text_input("Enter Ticket Number to Manage")
        if ticket_number:
            doc = tickets_collection.find_one({"ticket_number": ticket_number.strip()})
            if doc:
                current_status_db = doc.get("status", "Intake")
                current_status_ui = display_status(current_status_db)
                status_display_list = [display_status(s) for s in AVAILABLE_STATUSES]
                default_idx = status_display_list.index(current_status_ui) if current_status_ui in status_display_list else 0

                with st.form("edit_ticket_form"):
                    new_status_label = st.selectbox("Status", status_display_list, index=default_idx)
                    new_status_db = get_db_status_from_display(new_status_label)
                    new_subtickets = st.number_input("Sub-Tickets", min_value=1, value=int(doc.get("num_sub_tickets", 1)))
                    new_price = st.number_input("Ticket Price", min_value=0.0, value=float(doc.get("pay", 5.5)), step=0.5)

                    if st.form_submit_button("Update Ticket"):
                        tickets_collection.update_one(
                            {"ticket_number": ticket_number.strip()},
                            {
                                "$set": {
                                    "status": new_status_db,
                                    "num_sub_tickets": new_subtickets,
                                    "pay": new_price
                                }
                            }
                        )
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
            if st.button("Validate Tickets"):
                # We'll see which exist in DB vs not
                existing = []
                missing = []
                for t in ticket_list:
                    if tickets_collection.find_one({"ticket_number": t}):
                        existing.append(t)
                    else:
                        missing.append(t)

                if missing:
                    st.warning(f"{len(missing)} tickets not found: {', '.join(missing[:3])}{'...' if len(missing) > 3 else ''}")
                if existing:
                    st.success(f"{len(existing)} valid tickets found")
                st.stop()  # stops here so user can see the results

        # If user wants to process them in one go (without validation step):
        if st.button("Perform Bulk Action"):
            ticket_list = [t.strip() for t in bulk_tickets.split('\n') if t.strip()]
            if not ticket_list:
                st.warning("No valid tickets entered.")
            else:
                if bulk_action == "Update Status":
                    status_display_list = [display_status(s) for s in AVAILABLE_STATUSES]
                    new_status_label = st.selectbox("New Status", status_display_list)
                    new_status_db = get_db_status_from_display(new_status_label)
                    tickets_collection.update_many(
                        {"ticket_number": {"$in": ticket_list}},
                        {"$set": {"status": new_status_db}}
                    )
                    st.success(f"Updated {len(ticket_list)} tickets to {new_status_label}")
                elif bulk_action == "Change Price":
                    new_price = st.number_input("New Price", min_value=0.0, value=st.session_state.ticket_price)
                    tickets_collection.update_many(
                        {"ticket_number": {"$in": ticket_list}},
                        {"$set": {"pay": new_price}}
                    )
                    st.success(f"Updated pricing for {len(ticket_list)} tickets")
                elif bulk_action == "Add Subtickets":
                    add_count = st.number_input("Additional Subtickets", min_value=1, value=1)
                    # We'll do an update with $inc
                    tickets_collection.update_many(
                        {"ticket_number": {"$in": ticket_list}},
                        {"$inc": {"num_sub_tickets": add_count}}
                    )
                    st.success(f"Added {add_count} subtickets to {len(ticket_list)} tickets")

    # Tab 3: Delete Tickets
    with tab3:
        st.subheader("Ticket Deletion")
        delete_option = st.radio("Deletion Method", ["Single Ticket", "By Batch", "By Date Range"])
        if delete_option == "Single Ticket":
            del_ticket = st.text_input("Enter Ticket Number to Delete")
            if del_ticket and st.button("Delete Ticket"):
                result = tickets_collection.delete_one({"ticket_number": del_ticket.strip()})
                if result.deleted_count > 0:
                    st.success("Ticket deleted successfully")
                else:
                    st.error("Ticket not found or already deleted")
        elif delete_option == "By Batch":
            batch_name = st.text_input("Enter Batch Name to Delete")
            if batch_name and st.button("Delete Entire Batch"):
                result = tickets_collection.delete_many({"batch_name": batch_name.strip()})
                st.success(f"Deleted {result.deleted_count} tickets from batch {batch_name}")
        elif delete_option == "By Date Range":
            col_date1, col_date2 = st.columns(2)
            with col_date1:
                start_date = st.date_input("Start Date")
            with col_date2:
                end_date = st.date_input("End Date")
            if st.button("Delete Tickets in Date Range"):
                start_str = start_date.strftime("%Y-%m-%d")
                end_str = end_date.strftime("%Y-%m-%d")
                result = tickets_collection.delete_many({
                    "date": {"$gte": start_str, "$lte": end_str}
                })
                st.success(f"Deleted {result.deleted_count} tickets from {start_date} to {end_date}")

    # Tab 4: Manage Tickets By Batch
    with tab4:
        st.subheader("Manage Tickets By Batch Name")
        # distinct batches
        batch_names = tickets_collection.distinct("batch_name")
        if batch_names:
            selected_batch = st.selectbox("Select a Batch to Manage", batch_names)
            if selected_batch:
                docs = tickets_collection.find({"batch_name": selected_batch})
                df_batch = pd.DataFrame(list(docs))
                if not df_batch.empty:
                    df_batch['status'] = df_batch['status'].apply(display_status)
                    if "_id" in df_batch.columns:
                        df_batch.drop(columns=["_id"], inplace=True)
                    st.dataframe(df_batch, use_container_width=True)

                    # Bulk update
                    status_display_list = [display_status(s) for s in AVAILABLE_STATUSES]
                    new_status_label = st.selectbox("New Status for All Tickets in This Batch", status_display_list)
                    new_status_db = get_db_status_from_display(new_status_label)
                    if st.button("Update All Tickets in Batch"):
                        tickets_collection.update_many(
                            {"batch_name": selected_batch},
                            {"$set": {"status": new_status_db}}
                        )
                        st.success(f"All tickets in batch '{selected_batch}' updated to '{new_status_label}'!")
        else:
            st.info("No batches found in the database.")

    # Tab 5: Custom SQL Query Insert/Update
    # We don't really have direct SQL in Mongo, but let's mimic the functionality
    with tab5:
        st.subheader("Custom MongoDB Insert/Update")
        st.write("Enter a valid JSON-like command or a simple statement for insertion.")
        # For demonstration, let's keep it minimal:
        custom_query = st.text_area("Enter a pseudo-Mongo statement (like insertOne, updateMany, etc.)")
        if st.button("Execute Pseudo-Mongo Command"):
            st.warning("This is just a placeholder – in MongoDB, you typically run Python code, not raw SQL. Implement carefully if needed.")
            # Provide your own logic to parse or interpret the user's commands.

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

        # Collect all ticket_numbers in DB
        db_ticket_numbers = set(tickets_collection.distinct("ticket_number"))

        missing_in_db = user_tickets - db_ticket_numbers
        extra_in_db = db_ticket_numbers - user_tickets
        matches = user_tickets & db_ticket_numbers

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
            # Show details
            query_extra = {"ticket_number": {"$in": list(extra_in_db)}}
            docs_extra = tickets_collection.find(query_extra)
            df_extra = pd.DataFrame(list(docs_extra))
            if not df_extra.empty:
                df_extra["status"] = df_extra["status"].apply(display_status)
                if "_id" in df_extra.columns:
                    df_extra.drop(columns=["_id"], inplace=True)
                st.dataframe(df_extra, use_container_width=True)
        else:
            st.info("No extra tickets found in DB.")

        if matches:
            st.write("### Matched Tickets (In Both Lists)")
            query_match = {"ticket_number": {"$in": list(matches)}}
            docs_match = tickets_collection.find(query_match)
            df_matched = pd.DataFrame(list(docs_match))
            if not df_matched.empty:
                df_matched["status"] = df_matched["status"].apply(display_status)
                if "_id" in df_matched.columns:
                    df_matched.drop(columns=["_id"], inplace=True)
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

    raw_text = st.text_area(
        "Enter raw ticket data",
        placeholder="""125633 - Eastport-South Manor / Acer R752T
125632 - Eastport-South Manor / Acer R752T
125631 - Eastport-South Manor / Acer R752T""",
        height=200
    )

    display_list = [display_status(s) for s in AVAILABLE_STATUSES]
    target_status_label = st.selectbox("Select target status", display_list)
    target_status_db = get_db_status_from_display(target_status_label)

    if st.button("Generate and Execute Insert/Update"):
        lines = raw_text.strip().splitlines()
        ticket_numbers = []
        for line in lines:
            line = line.strip()
            if " - " in line:
                tnum = line.split(" - ")[0].strip()
                ticket_numbers.append(tnum)
            else:
                parts = line.split()
                if parts:
                    ticket_numbers.append(parts[0].strip())

        if ticket_numbers:
            # Insert or ignore (use upsert logic: insert if not exist)
            now_date = datetime.datetime.now().strftime("%Y-%m-%d")
            now_time = datetime.datetime.now().strftime("%H:%M:%S")
            for tkt in ticket_numbers:
                # We'll do an upsert:
                tickets_collection.update_one(
                    {"ticket_number": tkt},
                    {
                        "$setOnInsert": {
                            "date": now_date,
                            "time": now_time,
                            "batch_name": "Auto-Batch",
                            "num_sub_tickets": 1,
                            "pay": st.session_state.ticket_price,
                            "comments": "",
                            "ticket_day": "",
                            "ticket_school": ""
                        }
                    },
                    upsert=True
                )

            # 2) Update status to chosen status
            tickets_collection.update_many(
                {"ticket_number": {"$in": ticket_numbers}},
                {"$set": {"status": target_status_db}}
            )
            st.success(f"Inserted/updated {len(ticket_numbers)} tickets to '{target_status_label}'.")
        else:
            st.warning("No ticket numbers found in the input.")

# -----------------------------------------------------------
# Batches Page
# -----------------------------------------------------------
def batch_view_page():
    st.markdown("## 🗂️ Batch View")
    st.write("""Each batch is shown under the tab that matches its **single** status. 
    If a batch has multiple ticket statuses, it is shown as "Mixed" in the Mixed tab.""")

    # We want: batch_name, statuses, total_tickets, ticket_numbers
    pipeline = [
        {
            "$group": {
                "_id": "$batch_name",
                "statuses": {"$addToSet": "$status"},
                "total_tickets": {"$sum": "$num_sub_tickets"},
                "ticket_numbers": {"$push": "$ticket_number"}
            }
        }
    ]
    results = list(tickets_collection.aggregate(pipeline))
    df_batches = pd.DataFrame(results)
    if df_batches.empty:
        st.info("No batches found.")
        return

    df_batches.rename(columns={"_id": "batch_name"}, inplace=True)

    def get_batch_primary_status(row):
        stat_list = row["statuses"]
        if len(stat_list) == 1:
            return stat_list[0]
        return "Mixed"

    df_batches["batch_status"] = df_batches.apply(get_batch_primary_status, axis=1)

    known_statuses = AVAILABLE_STATUSES + ["Mixed"]
    tab_objects = st.tabs([display_status(s) for s in known_statuses])

    def display_batches_in_tab(df, container, tab_status):
        with container:
            df_filtered = df[df["batch_status"] == tab_status]
            if df_filtered.empty:
                st.info(f"No batches with status '{display_status(tab_status)}'")
                return
            cols = st.columns(3)
            for idx, row in df_filtered.iterrows():
                bname = row["batch_name"]
                statuses_raw = row["statuses"]
                total_tickets = row["total_tickets"]
                tnumbers = row["ticket_numbers"]

                if len(statuses_raw) == 1:
                    status_label = display_status(statuses_raw[0])
                else:
                    status_label = "Mixed"

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
                        # Simple approach: show them in a hidden input
                        random_suffix = f"copy_{bname}_{tab_status}"
                        tickets_str = ", ".join(tnumbers)
                        html_code = f"""
                        <input id="copyInput_{random_suffix}" 
                            type="text" 
                            value="{tickets_str}" 
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

    for status_key, tab_obj in zip(known_statuses, tab_objects):
        display_batches_in_tab(df_batches, tab_obj, status_key)

    if "edit_batch" in st.session_state and st.session_state["edit_batch"]:
        bname = st.session_state["edit_batch"]
        st.markdown("---")
        st.markdown(f"## Update Batch Status for: **{bname}**")
        docs_b = tickets_collection.find({"batch_name": bname})
        df_b = pd.DataFrame(list(docs_b))
        if not df_b.empty:
            df_b['status'] = df_b['status'].apply(display_status)
            if "_id" in df_b.columns:
                df_b.drop(columns=["_id"], inplace=True)
            st.dataframe(df_b, use_container_width=True)

        status_display_list = [display_status(s) for s in AVAILABLE_STATUSES]
        new_status_label = st.selectbox("New Status", status_display_list)
        new_status_db = get_db_status_from_display(new_status_label)
        if st.button("Confirm Status Update"):
            tickets_collection.update_many({"batch_name": bname}, {"$set": {"status": new_status_db}})
            st.success(f"All tickets in batch '{bname}' updated to '{new_status_label}'.")
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

    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    # SELECT date, SUM(num_sub_tickets * pay) AS day_earnings FROM tickets
    # WHERE status='Delivered' AND date BETWEEN ... GROUP BY date
    pipeline_delivered = [
        {"$match": {
            "status": "Delivered",
            "date": {"$gte": start_str, "$lte": end_str}
        }},
        {"$group": {
            "_id": "$date",
            "day_earnings": {"$sum": {"$multiply": ["$num_sub_tickets", "$pay"]}}
        }},
        {"$sort": {"_id": 1}}
    ]
    results_income = list(tickets_collection.aggregate(pipeline_delivered))
    df_income = pd.DataFrame(results_income)

    # SUM of pending
    pipeline_pending = [
        {"$match": {"status": {"$ne": "Delivered"}}},
        {"$group": {"_id": None, "pending_income": {"$sum": {"$multiply": ["$num_sub_tickets", "$pay"]}}}}
    ]
    results_pending = list(tickets_collection.aggregate(pipeline_pending))
    pending_income = results_pending[0]["pending_income"] if results_pending else 0

    if not df_income.empty:
        df_income.rename(columns={"_id": "date"}, inplace=True)
        df_income["date"] = pd.to_datetime(df_income["date"], format="%Y-%m-%d", errors="coerce")
        df_income.sort_values("date", inplace=True)

        fig = px.area(
            df_income,
            x="date",
            y="day_earnings",
            title="Daily Earnings Trend",
            labels={"day_earnings": "Earnings ($)", "date": "Date"}
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Detailed Earnings")
        st.dataframe(df_income, use_container_width=True)

        total_received = df_income["day_earnings"].sum()
        st.metric("Amount Received", f"${total_received:,.2f}")
        st.metric("Pending Income", f"${pending_income:,.2f}")
        st.metric("Total Potential Income", f"${(total_received + pending_income):,.2f}")

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
    st.write("This section provides AI-driven insights into your ticket management performance based on historical data.")

    # total tickets
    pipeline_total = [
        {"$group": {"_id": None, "total": {"$sum": "$num_sub_tickets"}}}
    ]
    result_total = list(tickets_collection.aggregate(pipeline_total))
    total_tickets = result_total[0]["total"] if result_total else 0

    # total delivered
    pipeline_delivered = [
        {"$match": {"status": "Delivered"}},
        {"$group": {"_id": None, "total_delivered": {"$sum": "$num_sub_tickets"}}}
    ]
    result_delivered = list(tickets_collection.aggregate(pipeline_delivered))
    total_delivered = result_delivered[0]["total_delivered"] if result_delivered else 0

    conversion_rate = (total_delivered / total_tickets * 100) if total_tickets else 0

    st.metric("Total Tickets", total_tickets)
    st.metric("Total Delivered", total_delivered)
    st.metric("Delivery Conversion Rate (%)", f"{conversion_rate:.2f}%")

    tab1, tab2, tab3, tab4 = st.tabs(["Daily Trend & Forecast", "Weekday Analysis", "Calendar Heatmap", "Anomaly Detection"])

    with tab1:
        pipeline_trend = [
            {"$match": {"status": "Delivered"}},
            {"$group": {
                "_id": "$date",
                "delivered": {"$sum": "$num_sub_tickets"}
            }},
            {"$sort": {"_id": 1}}
        ]
        results_trend = list(tickets_collection.aggregate(pipeline_trend))
        df_trend = pd.DataFrame(results_trend)
        if not df_trend.empty:
            df_trend.rename(columns={"_id": "date"}, inplace=True)
            df_trend['date'] = pd.to_datetime(df_trend['date'], format="%Y-%m-%d", errors="coerce")
            fig1 = go.Figure(go.Scatter(x=df_trend['date'], y=df_trend['delivered'], mode='lines+markers', name="Historical"))
            fig1.update_layout(title="Daily Delivered Tickets Trend", xaxis_title="Date", yaxis_title="Delivered Tickets")
            st.plotly_chart(fig1, use_container_width=True)

            avg_delivered = df_trend['delivered'].mean()
            st.write(f"On average, you deliver about {avg_delivered:.1f} tickets per day.")

            df_trend.sort_values("date", inplace=True)
            if len(df_trend) > 1:
                df_trend["date_num"] = df_trend["date"].map(datetime.datetime.toordinal)
                x = df_trend["date_num"].values
                y = df_trend["delivered"].values
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
        # We do a grouping by date and status, then break down by weekday
        pipeline_status = [
            {"$group": {
                "_id": {
                    "date": "$date",
                    "status": "$status"
                },
                "count": {"$sum": "$num_sub_tickets"}
            }}
        ]
        results_status = list(tickets_collection.aggregate(pipeline_status))
        df_status = pd.DataFrame(results_status)
        if not df_status.empty:
            df_status["date"] = pd.to_datetime(df_status["_id"].apply(lambda x: x["date"]), errors="coerce")
            df_status["status"] = df_status["_id"].apply(lambda x: x["status"])
            df_status.drop(columns=["_id"], inplace=True)

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
        # Calendar heatmap approach
        pipeline_del = [
            {"$match": {"status": "Delivered"}},
            {"$group": {
                "_id": "$date",
                "delivered": {"$sum": "$num_sub_tickets"}
            }}
        ]
        results_del = list(tickets_collection.aggregate(pipeline_del))
        df_delivered = pd.DataFrame(results_del)
        if not df_delivered.empty:
            df_delivered.rename(columns={"_id": "date"}, inplace=True)
            df_delivered['date'] = pd.to_datetime(df_delivered['date'], format="%Y-%m-%d", errors="coerce")
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
        pipeline_anomaly = [
            {"$match": {"status": "Delivered"}},
            {"$group": {
                "_id": "$date",
                "delivered": {"$sum": "$num_sub_tickets"}
            }},
            {"$sort": {"_id": 1}}
        ]
        results_anomaly = list(tickets_collection.aggregate(pipeline_anomaly))
        df_anomaly = pd.DataFrame(results_anomaly)
        if not df_anomaly.empty:
            df_anomaly.rename(columns={"_id": "date"}, inplace=True)
            df_anomaly['date'] = pd.to_datetime(df_anomaly['date'], errors="coerce")
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
        st.info("Your delivery conversion rate is below 50%. Consider strategies to improve ticket delivery.")
    elif conversion_rate < 75:
        st.info("Your delivery conversion rate is moderate. There might be room for improvement.")
    else:
        st.success("Great job! Your delivery conversion rate is high.")

    st.write("Keep monitoring your performance regularly to identify trends and optimize your operations.")

# -----------------------------------------------------------
# Backup & Restore Page
# -----------------------------------------------------------
def backup_restore_page():
    # This part was originally for .db files. We'll adapt it for MongoDB exports
    st.markdown("## 💾 Backup & Restore")
    st.write("Download your ticket data as an Excel file, or restore your ticket data from an Excel file. (MongoDB .db backups are not applicable here.)")

    st.subheader("Download Options")
    docs_all = list(tickets_collection.find({}))
    if docs_all:
        df_tickets = pd.DataFrame(docs_all)
        if "_id" in df_tickets.columns:
            df_tickets.drop(columns=["_id"], inplace=True)
        towrite = BytesIO()
        with pd.ExcelWriter(towrite, engine="xlsxwriter") as writer:
            df_tickets.to_excel(writer, index=False, sheet_name="Tickets")
        towrite.seek(0)
        st.download_button("Download Excel Backup", towrite.read(),
                           file_name="tickets_backup.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("No ticket data available to export.")

    st.markdown("---")
    st.subheader("Restore from Excel")
    st.write("Upload an Excel file to restore your ticket data. **Warning:** This will overwrite your current data in the `tickets` collection.")

    uploaded_excel = st.file_uploader("Choose an Excel file", type=["xlsx"])
    if uploaded_excel is not None:
        try:
            df_restore = pd.read_excel(uploaded_excel)
            required_columns = {"date", "time", "batch_name", "ticket_number", "num_sub_tickets", "status", "pay", "comments", "ticket_day", "ticket_school"}
            if not required_columns.issubset(set(df_restore.columns)):
                st.error("Uploaded Excel file does not contain the required columns.")
            else:
                # Clear existing
                tickets_collection.delete_many({})
                # Insert new
                records = df_restore.to_dict("records")
                tickets_collection.insert_many(records)
                st.success("Database restored successfully from Excel file!")
        except Exception as e:
            st.error(f"Error restoring from Excel: {e}")

    st.markdown("---")
    st.info("If you need a full MongoDB backup/restore, use MongoDB Tools (mongodump/mongorestore) or Atlas snapshots.")

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

    # Footer
    st.markdown(f"""
    <div style="text-align:center; padding: 15px; font-size: 0.8rem; border-top: 1px solid #ccc; margin-top: 30px;">
        <p>{st.session_state.company_name} Ticket System • {datetime.datetime.now().year}</p>
        <p>Powered by Streamlit • v1.0 • MongoDB Edition</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
