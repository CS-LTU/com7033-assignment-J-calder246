
import os
import sqlite3
from datetime import datetime

from flask import (
Flask, request, redirect, render_template, url_for, flash, session )
import bcrypt
import pandas as pd
from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField



#importations from python files

from config import Config
from db_sqlite import get_db
from bootstrap import bootstrap_once
from auth_utils import allowed_file, safe_save_upload
from decorators import login_required, admin_required
from services_admin import is_admin
from services_logging import log_action, stroke_collection


app = Flask(__name__, template_folder="templates")
app.secret_key = Config.SECRET_KEY

#esurses runtime folders and bootstaps DB/admin
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
bootstrap_once()

#______
#___Fix for not finding specific id
#______

@app.route("/patient/<pid>")
@login_required
def patient_record(pid):
    try:
        # MongoDB stores most values as strings, so ensure match type
        record = stroke_collection.find_one({"id": int(pid)})
    except Exception:
        record = None

    if not record:
        flash("Patient record not found.", "warning")
        return redirect(url_for("patientview"))

    return render_template("patientrecord.html", record=record)


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

        customer_id = request.form.get("id", "").strip()        
        username = request.form.get("username", "").strip()
        age = request.form.get("age", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not (customer_id and username and password and confirm_password and age):
            flash('All fields are required.', 'error')
            return render_template('registration.html')
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('registration.html')
        if not age.isdigit() or int(age) < 13:
            flash('Age must be a number and at least 13', 'error')
            return render_template('registration.html')
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('registration.html')
       

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        conn = None
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, customer_id, password_hash) VALUES (?, ?, ?)",
                (username, customer_id, hashed_password)
            )
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('ID already exists. Please choose a different one or login', 'error')
        except Exception as e:
            flash(f'Unexpected error during registration: {e}', 'danger')
        finally:
            if conn:
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
        cur.execute("""   SELECT _id, username, customer_id, password_hash
            FROM users
            WHERE username = ?
            """, (username,))
        user = cur.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
            session["username"] = user["username"]
            session["_id"] = user["_id"]
            session["customer_id"] = user["customer_id"]
            session["is_admin"] = is_admin(user["customer_id"])
            flash("Login successful!", "success")
            try:
                log_action("USER_LOGIN", user["customer_id"], {})
            except Exception as e:
                print(f"Logging failed: {e}")
            return redirect(url_for("admindashboard" if session["is_admin"] else "patientview"))
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
    cid = session.get("_id")
    session.clear()
    flash("Successfully logged out.", "info")
    if cid:
        log_action("LOGOUT", cid, {})
    return redirect(url_for("home"))

    #_____________
#_________________User view
#__________________
#______________
#ROUTE TO USER PROFILE
#_______________
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    uid = session.get("customer_id")
    conn = get_db()
    cur = conn.cursor()
    if request.method =="POST":
        username = request.form.get("username", "").strip()
        new_password = request.form.get("new_password", "")
        age = request.form.get("age", "").strip()

        if not (username and age.isdigit() and int(age) >= 13):
            flash("Invalid input. Please ensure all fields are correctly filled.", "danger")
            return redirect(url_for("profile"))
        try:
            if (new_password):
                if len(new_password) <8:
                    flash("password must be at least 8 characters long", "danger")
                    return redirect(url_for("profile"))
                pw_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                cur.execute("UPDATE users SET username = ?, age = ?, password_hash = ? WHERE id =?", (username, int(age), pw_hash, uid))
            else:
                cur.execute("UPDATE users SET username = ?, age = ?, WHERE id = ?", username, int(age), uid)
            conn.commit()
        except sqlite3.IntegrityError:
            flash("Username already exists. Please choose another.", "danger")
            conn.close()
            return redirect(url_for("profile"))
        session["username"] = username
        flash("Profile updated", "success")
        log_action("UPDATE_PROFILE", session.get("customer_id"), {"username": username})
    
    cur.execute("SELECT id, username customer_id, age FROM users WHERE id = ?", (uid))
    user = cur.fetchone()
    conn.close()
    return render_template("profile.html", user=user)

    
              

#route to user data
@app.route("/patientview")
@login_required
def patientview():
    customer_id = session.get("customer_id")
    
    if not customer_id:
        flash("Please log in to view patient data.", "warning")
        return redirect(url_for("login"))

    try:
        # Ensure we query using a string type (Mongo records often store customer_id as string)
        cid = str(customer_id)
        data = list(stroke_collection.find({"customer_id": cid}))
        # If no records found for this customer (common with local fallback where sample ids differ),
        # show available sample records so the UI can be inspected.
        if not data:
            try:
                data = list(stroke_collection.find())
                if data:
                    flash("No personal records found — showing available sample records.", "info")
            except Exception:
                data = []
        app.logger.debug("patientview: customer_id=%s records=%d", cid, len(data))
    except Exception as e:

        # If Mongo is unreachable (common in restricted/networked environments),
        # log the exception and show a small sample dataset so the UI can be inspected.
        app.logger.exception("Error fetching records for customer_id=%s: %s", customer_id, e)
        flash("Unable to reach the medical database — showing sample data for now.", "warning")
        data = [
            {"id": 1, "gender": "Female", "age": 68, "hypertension": 0, "heart_disease": 1, "stroke": 1, "customer_id": cid},
            {"id": 2, "gender": "Male", "age": 54, "hypertension": 1, "heart_disease": 0, "stroke": 0, "customer_id": cid},
        ]


    return render_template("patientview.html", data=data)


#_____________
#~~~~~~ADMIN TOOLS~~~~~~~~~
#_____________

#admin dashboard route
@app.route("/admindashboard")
@admin_required
def admindashboard():
    return render_template("admin/admindashboard.html")
#page only for admins

#route for admin to view users (sql)
@app.route("/admin/users")
@admin_required
def admin_view_users():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT _id, username, customer_id FROM users ORDER BY _id DESC")
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
    cur.execute("SELECT _id FROM users WHERE customer_id = ?", (customer_id,))
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

#________
#_fix for table not coming up
#_________
from services_logging import stroke_collection
try:
    print('count all', stroke_collection.count_documents({}))
except Exception as e:
    print('mongo error:', type(e).__name__, e)



#__________
#Run app
#________
if __name__ == "__main__":
    bootstrap_once()   #ensures admin account exists
    app.run(host="0.0.0.0", port=5869, debug=False)





