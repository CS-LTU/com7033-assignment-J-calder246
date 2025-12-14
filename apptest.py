from app4 import app
import unittest

'''
PAGES
Homes (/)
Login (/login)
Registration (/registration)
Admin Dashboard (/admin)
ad_create (/ad_create)
ad_patients (/ad_patients)
contact (/contact)
logout (/logout)
patient (/patient)
profile (/profile)


'''

class Flaskapptests(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.client = app.test_client()

    #test home
    def test_home_page(self):
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'<title>MyHealth Portal</title>', r.data)
        self.assertIn(b'<p>Securely access\n your medical Records with The Health Centre. "Because a healthy body, starts with healthy IT"</p>', r.data)

    #test registration
    def test_registration_page(self):
        r = self.client.get('/registration')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'<h2>User Registration</h2>', r.data)

    #testing login
    def test_login(self):
        r = self.client.get('/login')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'<h1>Health Centre</h1>', r.data)
        self.assertIn(b'<h2>User Login</h2>', r.data)

    #test for profile requiring login

    

    
    
    



#run test
unittest.main(argv=[''], verbosity=2, exit=False)
