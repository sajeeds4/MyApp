import streamlit as st
import sqlite3
import pandas as pd
import datetime

def run_query(query: str):
    """
    Executes the given SQL query against the local SQLite database.
    For SELECT queries, returns a DataFrame with the results.
    For non-SELECT queries, commits changes and returns a message including the number of rows affected.
    """
    try:
        conn = sqlite3.connect("ticket_management.db")
        cursor = conn.cursor()
        st.write("Executing query:", query)
        cursor.execute(query)
        
        if query.strip().lower().startswith("select"):
            data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(data, columns=columns)
            st.write("Query returned", len(df), "rows.")
            conn.close()
            return df, None
        else:
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            st.write("Query committed successfully. Rows affected:", affected)
            return None, f"Query executed successfully. Rows affected: {affected}"
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return None, f"Error: {e}"

def extension_page():
    st.markdown("## 🔍 SQL Query Console")
    st.write("Run custom SQL queries on your local SQLite database (ticket_management.db).")
    st.warning("Use caution with UPDATE, DELETE, or DROP queries as these can permanently modify your data.")

    query = st.text_area("Enter your SQL query below:", height=150,
                         placeholder="e.g., UPDATE tickets SET status = 'Delivered' WHERE ticket_number = 'T123';")
    
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
