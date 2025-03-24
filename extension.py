import streamlit as st
import sqlite3
import pandas as pd
import datetime

def run_query(query: str):
    """
    Executes the given SQL query against the local SQLite database.
    For SELECT queries, it returns a DataFrame.
    For non-SELECT queries, it commits changes and returns a success message.
    Debug information is printed if an error occurs.
    """
    try:
        conn = sqlite3.connect("ticket_management.db")
        cursor = conn.cursor()
        st.write("Executing query:", query)
        cursor.execute(query)
        
        # Check if it's a SELECT query
        if query.strip().lower().startswith("select"):
            data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(data, columns=columns)
            conn.close()
            st.write("Query returned", len(df), "rows.")
            return df, None
        else:
            conn.commit()
            conn.close()
            st.write("Query committed successfully.")
            return None, "Query executed successfully."
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return None, f"Error: {e}"

def extension_page():
    st.markdown("## 🔍 SQL Query Console")
    st.write("Run custom SQL queries on your local SQLite database (ticket_management.db).")
    st.warning("Use caution with UPDATE, DELETE, or DROP queries; these can permanently modify your data.")
    
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
    st.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
