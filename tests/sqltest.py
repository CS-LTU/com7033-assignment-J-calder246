import sqlite3
import os
import unittest

from db_sqlite import get_db


#connecting to db

db_path = "users.db"

conn = get_db()
cursor = conn.cursor()

#testing adding a user
cursor.execute('''
               INSERT INTO users (customer_id, username, password_hash)) VALUES (?, ?, ?)
               ''', ("testing000", "experimentaluser", "hashedpw123"))

conn.commit()
cursor.close()
conn.close()

#check user added

def user_exists(customer_id, username, password_hash):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    #executes query on user
    cursor.execute("SELECT * FROM users WHERE username = ? AND customer_id = ? AND password_hash = ?", (username, customer_id, password_hash))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result is not None

def setup(self):
    self.username = "experimentaluser"
    self.customer_id = "testing000"
    self.password_hash = "hashedpw123"

def test_user_exists(self):
    #tests user in the database
    self.assertTrue(user_exists(self.username, self.customer_id, self.password_hash), f"{self.username} should exist in the database")
    
def test_user_not_exist(self):
    #checks for user that hasn't been added
    self.assertFalse(user_exists('nonuser', 'noid', 'nopassword'), "nonuser shouldn't exist in the database")
    
#create db
if __name__ == '__main__':
    unittest.main(argv=[''], exit=False)


