
import os
import sqlite3
from datetime import datetime

from flask import (
Flask, request, redirect, render_template, url_for, flash, session )
import bcrypt
import pandas as pd

#importations from python files

from config import Config
from db_sqlite import get_db
from bootstrap import bootstrap_once
from auth_utils import allowed_file, safe_save_upload
from decorators import login_required, admin_required
from services_admin import is_admin
from services_logging import log_action, stroke_collection


app = Flask(__name__, template_folder="../templates")
app.secret_key = Config.SECRET_KEY

#esurses runtime folders and bootstaps DB/admin
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
bootstrap_once()

#----------
#ROUTE TO HOME
#___________


@app.route('/')
def home():
    return render_template('home.html')

#--------------------
#Registraation route
#_____________________
@app.route("/registration", methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        id = request.form.get("id", "").strip() #strip() removes black spaces
        username = request.form.get("username", "").strip()
        
        age = request.form.get("age", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm password", "").strip()

        if not (id and username and password and confirm_password):
            flash('All fields are required.', 'error')
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
        if not age.isdigit() or int(age) < 13:   #age>13 for GDPR  compliance (not data on kids)
            flash('age must be a number and at least 13', 'error')
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('registration.html')
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


        try:
            conn = get_db()
            cursor = conn.cursor()
    
            cursor.execute("INSERT INTO users (username, customer_id, password_hash) VALUES (?, ?, ?)", (username, id, hashed_password))
            conn.commit()
            conn.close()
            flash('Registration successful! Please log in.', 'success')
            return redirect('/login')
        except sqlite3.IntegrityError:
            flash('ID already exists. Please choose a different one. or login', 'error')
        finally:
            conn.close()
    return render_template('registration.html')

    
#________________
#Login page
#_________________

#log in
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""   SELECT id, username, password_hash
            FROM users
            WHERE username = ?
            """, (username,))
        user = cur.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].decode("utf-8")):
            session["username"] = user["username"]
            session["id"] = user["id"]
            session["is_admin"] = is_admin(user["customer_id"])
            flash("Login successful!", "success")
            log_action("USER_LOGIN", username, {})
            return redirect(url_for("index" if session["is_admin"] else "user.dashboard"))
        else:
            flash("Username and/or password not recognised", "danger")
            return redirect(url_for("login"))
    return render_template("login.html")

    #_______________
#LOGOUT ROUTE
#_________________

#logout
@app.route("/logout")
def logout():
    cid = session.get("customer_id")
    session.clear()
    flash("Successfully logged out.", "info")
    if cid:
        log_action("LOGOUT", cid, {})
    return redirect(url_for("home"))

    #_____________
#_________________User view
#__________________

#route to user data
@app.route("/patientview")
@login_required
def patientview():
    cid = session.get("customer_id")
    stroke_collection = get_db().stroke_records  
    try:
        records = list(stroke_collection.find({"customer_id": cid}))
    except Exception:
        records = []
    return render_template("patientview.html", records=records)


#_____________
#~~~~~~ADMIN TOOLS~~~~~~~~~
#_____________

#admin dashboard route
@app.route("/admindashboard")
@admin_required
def admindashboard():
    return render_template("dashboard.html")
#page only for admins

#route for admin to view users (sql)
@app.route("/admin/users")
@admin_required
def admin_view_users():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, username, customer_id FROM users ORDER BY id DESC")
    USERS = [dict(row) for row in cur.fetchall()]
    conn.close()

    #marks administrator flag for display
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT customer_id FROM admins")
    admin_cids = {r[0] for r in cur.fetchall()}#set of customerids (aadmin)
    conn.close()
    for user in USERS:
        user["is admin"] = user["customer_id"] in admin_cids
    return render_template("admin/users.html", users=USERS)


#_______
##ADDING CRUD FUNCTIONALITIES FOR ADMINS (create read update delete)
#________


@app.route("/admin/delete/<customer_id>", methods=["POST"])
@admin_required
def delete_user(customer_id):
    #code to prevent adaming delting him/her self
    admin_cid = session.get("customer_id")
    if customer_id == admin_cid:
        flash("You cannot delete your own admin account.", "danger")
        return redirect(url_for("admin_view_users"))
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE customer_id = ?", (customer_id))
    row = cur.fetchone()
    if not row:
          conn.close()
          flash("User not founder", "warning")
          return redirect(url_for("admin_view_users"))
    
    #delete from users (admin only)
    cur.execute("DELETE FROM users WHERE customer_id = ?", (customer_id,)) #deletes from table
    conn.commit()
    conn.close()

    try:
        stroke_collection.delete_many({"customer_id": customer_id})
    except Exception:
        pass
        
    flash("user and user info deleted", "success")
    log_action("DELETE_USER", admin_cid, {"deleted_customer_id": customer_id})
    return redirect(url_for("admin_view_users"))

#create user
@app.route("/admin/create", methods=["GET", "POST"])
@admin_required
def create_user():  
    if request.method == "POST":
       if 'file' not in request.files:
              flash("No file part", "danger")
              return redirect(request.url)
       file = request.files["file"]
       if file.filename == "":
            flash("No file has been selected", "danger")
            return redirect(request.url)
       if not allowed_file(file.filename):
            flash(" Incorrect file type, please upload a CSV file.", "danger")
            return redirect(request.url)
       
       path, filename = safe_save_upload(file, Config.UPLOAD_FOLDER)
       
    try:
        df = pd.read_csv(path)
        required = {"id", "gender", "age", "hypertension", "heart_disease", "ever_married", "work_type", "Residence_type", "avg_glucose_level", "bmi", "smoking_status", "stroke", "customer_id"} #CASE SENSITIVE
        cols = {c.lower().strip() for c in df.column}
        if not required.issubset(cols):
            flash("CSV is missing: '{', '.join(sorted(required))}", "danger")
            return redirect(request.url)
        #cleaning and setting headers
        df.columns = [c.lower().strip() for c in df.columns]
        df["id"] = pd.to_numeric(df["id"], errors="coerce").filna(1).astype(int)
        df["gender"] = pd.to_str(df["gender"]).fillna("Unknown").astype(str)
        df["age"] = pd.to_numeric(df["age"], errors="coerce").fillna(0).astype(int)
        df["hypertension"] = pd.to_numeric(df["hypertension"], errors="coerce").fillna(0).astype(int)
        df["heart_disease"] = pd.to_numeric(df["heart_disease"], errors="coerce").fillna(0).astype(int)
        df["ever_married"] = pd.to_str(df["ever_married"]).fillna("unknown").astype(str)
        df["work_type"] = pd.to_str(df["work_type"]).fillna("unknown").astype(str)
        df["residence_type"] = pd.to_str(df["residence_type"]).fillna("unknown").astype(str)
        df["avg_glucose_level"] = pd.to_numeric(df["avg_glucose_level"]).fillna(0).astype(float)
        df["bmi"] = pd.to_numeric(df["bmi"], errors="coerce").fillna(0).astype(float)
        df["smoking_status"] = pd.to_str(df["smoking_status"]).fillna("unknown").astype(str)
        df["stroke"] = pd.to_numeric(df["stroke"], errors="coerce").fillna(0).astype(int)


#recording id of editor
        records = df.to_dict(orient="records")
        for record in records:
            record["uploaded_by"] = session.get("customer_id")
            record["uploaded_ad"] = datetime.utcnow()
        if records:
            stroke_collection.insert_many(records)
        flash(f"Successfully uploaded {len(records)} records.", "success")
        log_action("UPLOAD_DATA", session.get("customer_id"), {"record_count": len(records)})
        return redirect(url_for("admindashboard"))
    except Exception as e:
        flash(f"Error processing file: {str(e)}", "danger")
        return redirect(request.url)
    return render_template("admin/upload.html")
       

#Route for admin's view
@app.route("/admin/patients")
@admin_required
def admin_view_patients():
    data = list(stroke_collection.find())
    return render_template("admin/patients.html", records=data)

#__________
#Run app
#________
if __name__ == "__main__":
    bootstrap_once()   #ensures admin account exists
    app.run(hosts="0.0.0.0", port=1010, debug=False)

    