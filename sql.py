from pathlib import Path
from sys import argv



import sqlite3
from config import Config
import os
import unittest  #used to test database at the end


#SQLite helper
def get_db():
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
    #opens users.db connection
def init_sqlite_db():
    conn = get_db()
    cur = conn.cursor()
    # Ensure users table has a stable schema. keep backwards compatibility
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users1(
        _id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        id INTEGER NOT NULL UNIQUE,
        password_hash TEXT NOT NULL
    )
    """)
    # make username unique
    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_unique
    ON users1(username)
    """)
    
    
    #making a table for admins
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins1(
                id TEXT PRIMARY KEY
    )
    """)
    conn.commit()
    conn.close()
