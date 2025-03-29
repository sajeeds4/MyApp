import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go
import plotly.express as px

from utils.animations import animations
from utils.status import ui_status_from_db

from streamlit_lottie import st_lottie

def dashboard_page(conn):
    cursor = conn.cursor()

    # Top animation and title
    col_anim, col_title = st.columns([1, 5])
    with col_anim:
        if animations["dashboard"]:
            st_lottie(animations["dashboard"], height=150, key="dash_anim")
    with col_title:
        st.markdown("## 📊 Real-Time Ticket Analytics")
        st.write("View and analyze your ticket performance and earnings at a glance.")
    
    # Totals
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

    # Display key metrics
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
        fig.update_layout(title='Daily Ticket Activity', xaxis_title='Date', yaxis_title='Number of Tickets',
                          hovermode='x unified', template='plotly_white', height=500)
        st.plotly_chart(fig, use_container_width=True)
        
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
            df_status['status_ui'] = df_status['status'].apply(ui_status_from_db)
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
        df_recent['status'] = df_recent['status'].apply(ui_status_from_db)
        st.dataframe(df_recent, use_container_width=True)
    else:
        st.info("No recent activity to display")
