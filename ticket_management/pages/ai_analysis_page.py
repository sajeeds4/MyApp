import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objects as go
import plotly.express as px

from utils.animations import animations
from utils.status import ui_status_from_db
from streamlit_lottie import st_lottie

def ai_analysis_page(conn):
    cursor = conn.cursor()

    st.markdown("## 🤖 AI Analysis")
    st.write("This section provides AI-driven insights into your ticket management performance based on historical data.")
    
    total_tickets_df = pd.read_sql("SELECT SUM(num_sub_tickets) as total FROM tickets", conn)
    total_tickets = total_tickets_df.iloc[0]['total'] or 0
    total_delivered_df = pd.read_sql("SELECT SUM(num_sub_tickets) as total_delivered FROM tickets WHERE status='Delivered'", conn)
    total_delivered = total_delivered_df.iloc[0]['total_delivered'] or 0
    conversion_rate = (total_delivered / total_tickets * 100) if total_tickets else 0

    st.metric("Total Tickets", total_tickets)
    st.metric("Total Delivered", total_delivered)
    st.metric("Delivery Conversion Rate (%)", f"{conversion_rate:.2f}%")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Daily Trend & Forecast", "Weekday Analysis", "Calendar Heatmap", "Anomaly Detection"])
    
    # Daily Trend & Forecast
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
                forecast_dates = [last_date + datetime.timedelta(days=i) for i in range(1, 7+1)]
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
    
    # Weekday Analysis
    with tab2:
        df_status = pd.read_sql(
            "SELECT date, status, SUM(num_sub_tickets) as count FROM tickets GROUP BY date, status",
            conn
        )
        if not df_status.empty:
            df_status['date'] = pd.to_datetime(df_status['date'])
            df_status['weekday'] = df_status['date'].dt.day_name()
            df_status['status_ui'] = df_status['status'].apply(ui_status_from_db)
            pivot = df_status.pivot_table(index='weekday', columns='status_ui', values='count', aggfunc='mean', fill_value=0)
            weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            pivot = pivot.reindex(weekday_order)
            st.subheader("Average Daily Ticket Counts by Weekday")
            st.dataframe(pivot)
            fig2 = go.Figure()
            for status in pivot.columns:
                fig2.add_trace(go.Bar(
                    x=pivot.index,
                    y=pivot[status],
                    name=status
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
    
    # Calendar Heatmap
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
    
    # Anomaly Detection
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
