# extension.py
"""
Extension module for additional functionalities in the Ticket Management System.
This module provides a disaster recovery function that migrates your local SQLite data to a Supabase Postgres database.
Both databases can be used concurrently.
"""

import streamlit as st
import sqlite3
import psycopg2
from dotenv import load_dotenv
import os
import datetime

# Load environment variables from .env (if present)
load_dotenv()

# Supabase connection details (Direct Connection)
# Update these in your .env file if desired.
SUPABASE_USER = os.getenv("SUPABASE_USER", "postgres")
SUPABASE_PASSWORD = os.getenv("SUPABASE_PASSWORD", "1234")  # Your password is 1234
SUPABASE_HOST = os.getenv("SUPABASE_HOST", "db.libemlugyexqnwtobjsk.supabase.co")
SUPABASE_PORT = os.getenv("SUPABASE_PORT", "5432")
SUPABASE_DBNAME = os.getenv("SUPABASE_DBNAME", "postgres")

def connect_to_supabase():
    """
    Connects to the Supabase Postgres database using psycopg2.
    """
    try:
        connection = psycopg2.connect(
            user=SUPABASE_USER,
            password=SUPABASE_PASSWORD,
            host=SUPABASE_HOST,
            port=SUPABASE_PORT,
            dbname=SUPABASE_DBNAME
        )
        return connection
    except Exception as e:
        st.error(f"Failed to connect to Supabase: {e}")
        return None

def migrate_data_to_supabase():
    """
    Migrates all records from the local SQLite 'tickets' table to the Supabase 'tickets' table.
    This function assumes that the Supabase 'tickets' table schema matches the SQLite schema.
    The SQLite table is assumed to have columns:
      id, date, time, batch_name, ticket_number, num_sub_tickets, status, pay, comments, ticket_day, ticket_school
    The 'id' column (first column) is skipped in the insertion.
    """
    try:
        # Connect to local SQLite database and fetch all records
        sqlite_conn = sqlite3.connect("ticket_management.db")
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT * FROM tickets")
        rows = sqlite_cursor.fetchall()
        sqlite_conn.close()

        if not rows:
            st.warning("No data found in the local SQLite database.")
            return

        # Prepare data for insertion: skip the 'id' column from SQLite (first element of each row)
        values_to_insert = [row[1:] for row in rows]

        # Connect to Supabase Postgres database
        supabase_conn = connect_to_supabase()
        if supabase_conn is None:
            return
        supabase_cursor = supabase_conn.cursor()

        # Insert data into the Supabase table 'tickets'
        # Using ON CONFLICT DO NOTHING to avoid duplicate key errors (assumes ticket_number is unique)
        insert_query = """
            INSERT INTO tickets (date, time, batch_name, ticket_number, num_sub_tickets, status, pay, comments, ticket_day, ticket_school)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ticket_number) DO NOTHING;
        """
        supabase_cursor.executemany(insert_query, values_to_insert)
        supabase_conn.commit()
        supabase_cursor.close()
        supabase_conn.close()

        st.success(f"Successfully migrated {len(values_to_insert)} records to Supabase.")
    except Exception as e:
        st.error(f"An error occurred during migration: {e}")

def extension_page():
    """
    Renders the Supabase disaster recovery page.
    This page provides an option to migrate your local SQLite data to Supabase.
    """
    st.markdown("## 🔧 Supabase Disaster Recovery")
    st.write("Migrate your local SQLite data to Supabase as a disaster recovery measure.")
    
    now = datetime.datetime.now()
    st.write(f"Current Date & Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    st.markdown("### Supabase Connection Details (Direct Connection)")
    st.write(f"**Host:** {SUPABASE_HOST}")
    st.write(f"**Port:** {SUPABASE_PORT}")
    st.write(f"**Database:** {SUPABASE_DBNAME}")
    st.write("**User:** postgres")
    st.write("**Password:** [REDACTED]")  # For security reasons, don't display the password.
    
    if st.button("Migrate Data to Supabase"):
        migrate_data_to_supabase()
