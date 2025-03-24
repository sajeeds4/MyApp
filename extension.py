# extension.py
"""
Extension module for additional functionalities in the Ticket Management System.
This module includes functionality for migrating your local SQLite data to Supabase,
providing disaster recovery. Both databases can be used simultaneously.
"""

import streamlit as st
import sqlite3
import datetime
import os
from supabase import create_client, Client

# Set your Supabase credentials (update these with your actual credentials or set them as environment variables)
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-supabase-url.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your-supabase-key")

# Create a Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def migrate_data_to_supabase():
    """
    Migrates all records from the local SQLite 'tickets' table to the Supabase 'tickets' table.
    Assumes that the Supabase table schema matches the SQLite table schema.
    """
    try:
        # Connect to the local SQLite database
        conn = sqlite3.connect("ticket_management.db")
        cursor = conn.cursor()

        # Fetch all data from the 'tickets' table
        cursor.execute("SELECT * FROM tickets")
        rows = cursor.fetchall()

        # Retrieve column names from the SQLite table
        columns = [description[0] for description in cursor.description]
        # Convert each row into a dictionary mapping column names to values
        data = [dict(zip(columns, row)) for row in rows]

        conn.close()

        if not data:
            st.warning("No data found in SQLite to migrate.")
            return

        # Insert data into the Supabase table (ensure the table 'tickets' exists on Supabase)
        response = supabase.table("tickets").insert(data).execute()

        # Check for a successful response (status code 200 or 201)
        if response.status_code in (200, 201):
            st.success(f"Successfully migrated {len(data)} records to Supabase.")
        else:
            st.error(f"Migration failed with status code: {response.status_code}. Response: {response.data}")
    except Exception as e:
        st.error(f"An error occurred during migration: {e}")

def extension_page():
    """
    Renders the extension page that provides Supabase migration functionality.
    """
    st.markdown("## 🔧 Extension Page: Supabase Disaster Recovery")
    st.write("Use this page to migrate your local SQLite data to Supabase for disaster recovery purposes.")
    
    st.info("Ensure your Supabase credentials are properly set in your environment or in the code.")
    
    # Show the current date and time as reference
    now = datetime.datetime.now()
    st.write(f"Current Date & Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Button to trigger data migration
    if st.button("Migrate Data to Supabase"):
        migrate_data_to_supabase()
    
    st.markdown("### Supabase Connection Details")
    st.write(f"Supabase URL: {SUPABASE_URL}")
    st.write("Supabase Key: [REDACTED]")  # For security reasons, do not display your key
