'''
import sqlite3
import unittest


class TestUserDatabase(unittest.TestCase):
    def setUp(self):
        # use an in-memory DB for tests to avoid touching the app database
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        self.cur.execute(
            
CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                customer_id TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
        )
        self.username = 'experimentaluser'
        self.customer_id = 'testing000'
        self.password_hash = 'hashedpw123'
        self.cur.execute(
            'INSERT INTO users (username, customer_id, password_hash) VALUES (?, ?, ?)',
            (self.username, self.customer_id, self.password_hash)
        )
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def user_exists(self, username, customer_id, password_hash):
        cur = self.conn.cursor()
        cur.execute(
            'SELECT 1 FROM users WHERE username = ? AND customer_id = ? AND password_hash = ?',
            (username, customer_id, password_hash)
        )

        return cur.fetchone() is not None

    def test_user_exists(self):
        self.assertTrue(self.user_exists(self.username, self.customer_id, self.password_hash))

    def test_user_not_exist(self):
        self.assertFalse(self.user_exists('noone', 'noid', 'nopw'))


if __name__ == '__main__':
    unittest.main()

'''