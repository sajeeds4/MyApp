import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.express as px
import plotly.graph_objects as go

from utils.animations import animations
from streamlit_lottie import st_lottie

def income_page(conn):
    cursor = conn.cursor()

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
