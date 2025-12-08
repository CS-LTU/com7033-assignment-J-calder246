#importing necessary libraies
from flask import Flask, request, redirect, render_template, flash, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
app = Flask(__name__)
app.secret_key = os.urandom(24) #sets up a random secret key, essential for CSRF protection and message flashing
#Initialising sql database: creases an sql file named patients.db in sql and defines attributes, id is the short id from the mongoDB table
def init_db():
    conn = sqlite3.connect('sql/patients.db')
    cursor = conn.cursor()
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY UNIQUE,
                        email TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL
                      )''')
    cursor.execute("""
                   CREATE UNIQUE INDEX IF NOT EXISTS IDX_USERS_EMAIL_NOCASE
                   ON users (lower(email));
                   """)  # makes email case-sensitive)
    conn.commit()
    conn.close()
    #route for registration page
@app.route('/')
def register():
    return render_template('registration.html')
    #handling user ragistration
    # @app.route('/register', methods=['POST'])
def do_register():
    id = request.form.get("id", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

        # basic validation
    if not (id and email and password):
        flash("All fields are required.")
        return redirect(url_for('register'))
    if len(password) < 6:
            flash("Password must be at least 6 characters long.")
            return redirect(url_for('register'))
    password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    conn = sqlite3.connect('sql/patients.db')
    cursor = conn.cursor()

    #checking for duplicates
    #duplicate id
    cursor.execute("SELECT 1 FROM users WHERE id = ?", (id,))
    if cursor.fetchone():
        flash("User ID already in use.")
        conn.close()
        return redirect(url_for('register'))
    #duplicate email
    cursor.execute("SELECT 1 FROM users WHERE lower(email) = lower(?)", (email,))
    if cursor.fetchone():
        flash("Email already in use.")
        conn.close()
        return redirect(url_for('register'))
    #inseryting user into sql db
    try:
        cursor.execute("INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)", (id, email, password_hash))
        conn.commit()
        flash("Registrations successful")
    except sqlite3.IntegrityError:
        flash("Email already in use, plrease register with a different one or log in.")
    finally:
        conn.close()
        return redirect(url_for('users'))

    
            


        
