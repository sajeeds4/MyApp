import sqlite3

def get_db_connection():
    conn = sqlite3.connect("ticket_management.db", check_same_thread=False)
    return conn

def setup_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        time TEXT,
        batch_name TEXT,
        ticket_number TEXT UNIQUE,
        num_sub_tickets INTEGER DEFAULT 1,
        status TEXT DEFAULT 'Intake',
        pay REAL DEFAULT 5.5,
        comments TEXT DEFAULT '',
        ticket_day TEXT,
        ticket_school TEXT
    )
    ''')
    conn.commit()
    conn.close()
