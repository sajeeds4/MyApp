import socket
import psycopg2
import streamlit as st

def connect_to_supabase_ipv4():
    try:
        # Resolve the IPv4 address of your Supabase host
        ipv4_address = socket.gethostbyname("db.libemlugyexqnwtobjsk.supabase.co")
        st.write(f"Using IPv4 address: {ipv4_address}")
        
        connection = psycopg2.connect(
            user="postgres",
            password="1234",  # Your password
            host=ipv4_address,
            port="5432",
            dbname="postgres"
        )
        st.success("IPv4 connection successful!")
        return connection
    except Exception as e:
        st.error(f"Failed to connect via IPv4: {e}")
        return None
