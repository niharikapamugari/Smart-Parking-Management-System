import sqlite3

def connect_db():
    conn = sqlite3.connect("parking.db", check_same_thread=False)
    return conn

def create_table():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_number TEXT,
        slot_number INTEGER,
        entry_time TEXT,
        exit_time TEXT,
        fee REAL,
        vehicle_type TEXT
    )
    """)

    conn.commit()
    conn.close()