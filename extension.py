import streamlit as st
import sqlite3
import pandas as pd
import datetime

def run_query(query: str):
    """
    Executes the given SQL query against the local SQLite database.
    If the query is a SELECT, it returns a DataFrame with the results.
    Otherwise, it commits the changes.
    """
    try:
        conn = sqlite3.connect("ticket_management.db")
        cursor = conn.cursor()
        cursor.execute(query)
        # Check if query is a SELECT query
        if query.strip().lower().startswith("select"):
            data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(data, columns=columns)
            conn.close()
            return df, None
        else:
            conn.commit()
            conn.close()
            return None, "Query executed successfully."
    except Exception as e:
        return None, str(e)

def extension_page():
    st.markdown("## 🔍 SQL Query Console")
    st.write("Run custom SQL queries on your local SQLite database (ticket_management.db).")
    st.write("**Warning:** Use caution when running UPDATE, DELETE, or DROP queries. This is intended for advanced users.")
    
    query = st.text_area("Enter your SQL query below:", height=150, placeholder="e.g., SELECT * FROM tickets;")
    
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

    st.markdown("### Recent Query Activity")
    st.write(f"Last run at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
