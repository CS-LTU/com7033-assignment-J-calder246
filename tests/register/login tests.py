'''
import unittest
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app4 import app


class FlaskAppTests(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.client = app.test_client()

    def test_registration_page(self):
        r = self.client.get('/registration')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'User Registration', r.data)

    def test_login_page(self):
        r = self.client.get('/login')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'User Login', r.data)


if __name__ == '__main__':
    unittest.main(argv=[''], verbosity=2, exit=False)
    
'''