"""
extension.py
------------
Extension module for additional functionalities in the Ticket Management System.
This module provides a disaster recovery function that migrates your local SQLite data
to a Supabase Postgres database. Both databases are available concurrently.
"""

import streamlit as st
import sqlite3
import psycopg2
from dotenv import load_dotenv
import os
import socket
import datetime

# Load environment variables from .env (if available)
load_dotenv()

# Supabase connection details (Direct Connection using IPv4)
SUPABASE_USER = os.getenv("SUPABASE_USER", "postgres")
SUPABASE_PASSWORD = os.getenv("SUPABASE_PASSWORD", "1234")  # Your password is "1234"
SUPABASE_HOST = os.getenv("SUPABASE_HOST", "db.libemlugyexqnwtobjsk.supabase.co")
SUPABASE_PORT = os.getenv("SUPABASE_PORT", "5432")
SUPABASE_DBNAME = os.getenv("SUPABASE_DBNAME", "postgres")

def get_ipv4_address(host: str) -> str:
    """
    Resolves and returns the IPv4 address for the given host.
    """
    try:
        ipv4_address = socket.gethostbyname(host)
        return ipv4_address
    except Exception as e:
        st.error(f"Error resolving IPv4 address for host {host}: {e}")
        return host

def connect_to_supabase():
    """
    Connects to the Supabase Postgres database using psycopg2 with IPv4 resolution.
    """
    try:
        ipv4_host = get_ipv4_address(SUPABASE_HOST)
        connection = psycopg2.connect(
            user=SUPABASE_USER,
            password=SUPABASE_PASSWORD,
            host=ipv4_host,
            port=SUPABASE_PORT,
            dbname=SUPABASE_DBNAME
        )
        st.write("Connected to Supabase via IPv4:", ipv4_host)
        return connection
    except Exception as e:
        st.error(f"Failed to connect to Supabase: {e}")
        return None

def migrate_data_to_supabase():
    """
    Migrates all records from the local SQLite 'tickets' table to the Supabase 'tickets' table.
    The first column (id) is skipped, and duplicate ticket numbers are ignored.
    """
    try:
        # Connect to local SQLite and fetch all records from 'tickets'
        sqlite_conn = sqlite3.connect("ticket_management.db")
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT * FROM tickets")
        rows = sqlite_cursor.fetchall()
        columns = [desc[0] for desc in sqlite_cursor.description]
        sqlite_conn.close()

        if not rows:
            st.warning("No data found in the local SQLite database.")
            return

        # Prepare data for insertion by skipping the 'id' column (assumed to be first)
        values_to_insert = [row[1:] for row in rows]

        # Connect to Supabase
        supabase_conn = connect_to_supabase()
        if supabase_conn is None:
            return
        supabase_cursor = supabase_conn.cursor()

        # Insert query – adjust the column order as needed.
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
    Provides an option to migrate your local SQLite data to Supabase.
    """
    st.markdown("## 🔧 Supabase Disaster Recovery")
    st.write("Migrate your local SQLite data to Supabase as a disaster recovery measure.")

    now = datetime.datetime.now()
    st.write(f"Current Date & Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

    st.markdown("### Supabase Connection Details (Direct Connection using IPv4)")
    resolved_host = get_ipv4_address(SUPABASE_HOST)
    st.write(f"**Host:** {SUPABASE_HOST} (resolved as {resolved_host})")
    st.write(f"**Port:** {SUPABASE_PORT}")
    st.write(f"**Database:** {SUPABASE_DBNAME}")
    st.write("**User:** postgres")
    st.write("**Password:** [REDACTED]")  # Do not display the actual password for security

    if st.button("Migrate Data to Supabase"):
        migrate_data_to_supabase()
