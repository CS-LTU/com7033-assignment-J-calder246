'''

import sqlite3
from unittest import result
from config import Config
import os
import unittest  #used to test database at the end

from db_sqlite import get_db, init_sqlite_db

from pathlib import Path
from sys import argv



import sqlite3
from config import Config
import os
import unittest  #used to test database at the end



create_database

#_______
    #INSERT USER FOR TEST
    #_______
    cur.execute(
    INSERT INTO users (username, customer_id, password_hash) VALUES (?, ?, ?)
    , ('username', '13240', 'hashedpassword1'))
    conn.commit()
    cur.close()
    conn.close()

    #test user is there
    def user_exists(username, customer_id, passwordhash):
        conn = sqlite3.connect('user.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?, customer_id = ?, password_hash = ?", (username, customer_id, passwordhash))
        result = cur.fetchone()
        cur.close()
        conn.close()
    return result is not None

#test
    class TestUserExists(unittest.TestCase):
        def setUp(self):
            self.username = 'username'
            self.customer_id = '13240'
            self.passwordhash = 'hashedpassword1'
        def test_userexists(self):
            self.assertTrue(user_exists(self.username, self.customer_id, self.passwordhash), f"{self.username} should be in database")
    #check for user not in db
    def test_non_user(self):
        self.assertFalse(user_exists('NonExistentUser', '01010', 'nohashedpw0'), 'NonExistentUser should not be in database')



    if __name__ == '__main__':
        unittest.main(argv=[''], exit=False)
'''
