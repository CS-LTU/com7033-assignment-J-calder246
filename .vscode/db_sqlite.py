

import sqlite3
from config import Config


#SQLite helper
def get_db():
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
    #opens users.db connection
def init_sqlite_db():
    conn = get_db()
    cur = conn.cursor()
    #table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT
    id TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL,
    password_hash TEXT NOT NULL
    )
    """)
    #make username unique
    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_unique
    ON users(username)
    """)
    
    #admin table
    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_admins_username_unique
                ON users(username)
                """)
    #making a table for admins
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins(
                id TEXT PRIMARY KEY
    )
    """)
    conn.commit()
    conn.close()
