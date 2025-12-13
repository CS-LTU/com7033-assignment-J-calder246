import os
import sqlite3
from datetime import datetime

from bson.objectid import ObjectId
from flask import (
    Flask, request, redirect, render_template, url_for, flash, session
)
import bcrypt
import pandas as pd



# local imports
from config import Config
from db_sqlite import get_db
from bootstrap import bootstrap_once
from auth_utils import allowed_file, safe_save_upload
from decorators import login_required, admin_required
from services_admin import is_admin
from services_logging import log_action





# resources runtime folders and bootstraps DB/admin
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
bootstrap_once()

app = Flask(__name__)
app.secret_key = 'Secret_key'

# stroke_collection and logs_collection are provided by services_logging
try:
    from services_logging import stroke_collection, logs_collection
except Exception:
    stroke_collection = None
    logs_collection = None




@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method =='POST':
        file = request.files['file']
        if file and file.filename.endswith('.csv'):
            df = pd.read_csv(file)
            records = df.to_dict(orient='records')
            stroke_collection.insert_many(records)
            flash('data successfully stored', "success")
            return redirect(url_for('home'))
        else:
            flash('invalid file type, please upload a CSV file', "danger")
            return redirect(request.url)
        return render_template('upload.html')

# ---------- ROUTES ----------
@app.route('/')
def home():
    return render_template('home.html')

# --------------------
# Registration route
# --------------------
@app.route("/registration", methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        customer_id = request.form.get("id", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not (customer_id and username and password and confirm_password):
            flash('All fields are required.', 'error')
            return render_template('registration.html')
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
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

# ----------------
# Login page
# ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT rowid AS _id, username, customer_id, password_hash
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
                app.logger.debug(f"Logging failed: {e}")
            return redirect(url_for("admindashboard" if session["is_admin"] else "profile"))
        else:
            flash("Username and/or password not recognised", "danger")
            return redirect(url_for("login"))
    return render_template("login.html")

# ---------------
# Logout
# ---------------
@app.route("/logout")
def logout():
    cid = session.get("customer_id")
    session.clear()
    flash("Successfully logged out.", "info")
    if cid:
        try:
            log_action("LOGOUT", cid, {})
        except Exception:
            pass
    return redirect(url_for("home"))

# ---------------
# Profile
# ---------------
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    uid = session.get("customer_id")
    conn = get_db()
    cur = conn.cursor()
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        new_password = request.form.get("new_password", "")
        age = request.form.get("age", "").strip()

        if not (username and age.isdigit() and int(age) >= 13):
            flash("Invalid input. Please ensure all fields are correctly filled.", "danger")
            return redirect(url_for("profile"))
        try:
            if new_password:
                if len(new_password) < 8:
                    flash("Password must be at least 8 characters long", "danger")
                    return redirect(url_for("profile"))
                pw_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                cur.execute("UPDATE users SET username = ?, age = ?, password_hash = ? WHERE customer_id = ?", (username, int(age), pw_hash, uid))
            else:
                cur.execute("UPDATE users SET username = ?, age = ? WHERE customer_id = ?", (username, int(age), uid))
            conn.commit()
        except sqlite3.IntegrityError:
            flash("Username already exists. Please choose another.", "danger")
            conn.close()
            return redirect(url_for("profile"))
        session["username"] = username
        flash("Profile updated", "success")
        try:
            log_action("UPDATE_PROFILE", session.get("customer_id"), {"username": username})
        except Exception:
            pass

    cur.execute("SELECT rowid AS id, username, customer_id, age FROM users WHERE customer_id = ?", (uid,))
    user = cur.fetchone()
    conn.close()
    return render_template("profile.html", user=user)

# -------------------------
# patientdata - search page
# -------------------------
@app.route("/patient")
@login_required
def patient():
    customer_id = session.get("customer_id")

    if not customer_id:
        flash("No customer ID found in session.", "danger")
        return redirect(url_for("profile"))

    # Try matching Mongo 'id' as integer
    record = None
    try:
        record = stroke_collection.find_one({"id": int(customer_id)})
    except Exception:
        pass
    # fallback: try string match
    if not record:
        record = stroke_collection.find_one({"id": str(customer_id)})

    # fallback: try customer_id field (not usually in dataset, but safe)
    if not record:
        record = stroke_collection.find_one({"customer_id": str(customer_id)})
   
    if not record:
        flash("No medical record found for your registered ID.", "warning")
        return redirect(url_for("profile"))

    return render_template("patient.html", record=record)

# -------------------------


# -------------
# ADMIN PAGES
# -------------
@app.route("/admindashboard")
@admin_required
def admindashboard():
    return render_template("admindashboard.html")

@app.route("/ad_patients")
@admin_required
def index():
    #gets all data from strokedata collection
    docs = list(stroke_collection.find())
    for doc in docs:
        doc['_id'] = str(doc['_id'])  #converts objectid to string not regular id
        return render_template('ad_patients.html', records=docs)
#__________________
#DELETE USER
# Admin delete route with parameter in URL
@app.route("/ad_patients", methods=["POST"])
@admin_required
def delete_user():
    stroke_collection.delete_one({"customer_id": request.form.get("customer_id")})
    return redirect(url_for("ad_patients"))
#__________________
#UPDATE USER
#__________________
@app.route("/ad_update", methods=["GET"])
@admin_required
def update_user():
    doc = stroke_collection.find_one({"_id_": ObjectId(id)})  #bases update of objectid (_id)
    
    if not doc:
        flash("User not found.", "danger")
        return redirect(url_for("ad_patients"))
    doc['_id'] = str(doc['_id'])
    return render_template("ad_update.html", record=doc)
#handle edit submit and selct what to change
@app.route("/ad_update_submit", methods=["POST"])
@admin_required
def update_user_submit():
    id = request.form.get("id")
    gender = request.form.get("gender")
    age = request.form.get("age")
    hypertension = request.form.get("hypertension")
    heart_disease = request.form.get("heart_disease")
    ever_married = request.form.get("ever_married")
    work_type = request.form.get("work_type")
    Residence_type = request.form.get("Residence_type")
    avg_glucose_level = request.form.get("avg_glucose_level")
    bmi = request.form.get("bmi")
    smoking_status = request.form.get("smoking_status")
    stroke = request.form.get("stroke")

    updated_data = {
        "id" : int(id),
        "gender" : gender,
        "age" : int(age),
        "hypertension" : int(hypertension),
        "heart_disease" : int(heart_disease),
        "ever_married" : int(ever_married),
        "work_type" : int(work_type),
        "Residence_type" : int(Residence_type),
        "avg_glucose_level" : (avg_glucose_level),
        "bmi" : bmi,
        "smoking_status": int(smoking_status),
        "stroke" : int(stroke)
        }

    stroke_collection.update_one({"_id": ObjectId(id)}, {"$set": updated_data})
    flash("User records have been updated.", "success")
    return redirect(url_for("ad_patients"))

#___________
#create user
#___________
@app.route('/ad_create')
@admin_required
def create_user():
    return render_template('ad_create.html')
#handle the submission
@app.route('/ad_create', methods=['POST'])
@admin_required
def add_record():
    id = request.form.get("id")
    gender = request.form.get("gender")
    age = request.form.get("age")
    hypertension = request.form.get("hypertension")
    heart_disease = request.form.get("heart_disease")
    ever_married = request.form.get("ever_married")
    work_type = request.form.get("work_type")
    Residence_type = request.form.get("Residence_type")
    avg_glucose_level = request.form.get("avg_glucose_level")
    bmi = request.form.get("bmi")
    smoking_status = request.form.get("smoking_status")
    stroke = request.form.get("stroke")

    updated_data = {
        "id" : int(id),
        "gender" : gender,
        "age" : int(age),
        "hypertension" : int(hypertension),
        "heart_disease" : int(heart_disease),
        "ever_married" : int(ever_married),
        "work_type" : int(work_type),
        "Residence_type" : int(Residence_type),
        "avg_glucose_level" : (avg_glucose_level),
        "bmi" : bmi,
        "smoking_status": int(smoking_status),
        "stroke" : int(stroke)
        }
    #inserting
    stroke_collection.insert_one(updated_data)
    flash("New user created successfully.", "success")
    return redirect(url_for("ad_patients"))



#______________________
#ADMIN UPLOADS CSV
#______________________
@app.route("/ad_update", methods=["GET", "POST"])

# Admin CSV upload / create user - simplified & safer
@app.route("/ad_create", methods=["GET", "POST"])
@admin_required
def create():
    if request.method == "POST":
        if 'file' not in request.files:
            flash("No file part", "danger")
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            flash("No file has been selected", "danger")
            return redirect(request.url)
        if not allowed_file(file.filename):
            flash("Incorrect file type, please upload a CSV file.", "danger")
            return redirect(request.url)

        path, filename = safe_save_upload(file, Config.UPLOAD_FOLDER)
        try:
            df = pd.read_csv(path)
            # required headers expected (case sensitive in original code)
            required = {"id", "gender", "age", "hypertension", "heart_disease", "ever_married",
                        "work_type", "Residence_type", "avg_glucose_level", "bmi", "smoking_status", "stroke", "customer_id"}
            cols = {c.lower().strip() for c in df.columns}
            if not required.issubset(cols):
                flash("CSV is missing required columns.", "danger")
                return redirect(request.url)

            # cleaning and converting columns (basic safe approaches)
            df.columns = [c.lower().strip() for c in df.columns]
            df["id"] = pd.to_numeric(df["id"], errors="coerce").fillna(0).astype(int)
            df["gender"] = df["gender"].astype(str).fillna("Unknown")
            df["age"] = pd.to_numeric(df["age"], errors="coerce").fillna(0).astype(int)
            df["hypertension"] = pd.to_numeric(df["hypertension"], errors="coerce").fillna(0).astype(int)
            df["heart_disease"] = pd.to_numeric(df["heart_disease"], errors="coerce").fillna(0).astype(int)
            df["ever_married"] = df["ever_married"].astype(str).fillna("unknown")
            df["work_type"] = df["work_type"].astype(str).fillna("unknown")
            df["residence_type"] = df.get("residence_type", df.get("Residence_type", pd.Series())).astype(str).fillna("unknown")
            df["avg_glucose_level"] = pd.to_numeric(df["avg_glucose_level"], errors="coerce").fillna(0.0).astype(float)
            df["bmi"] = pd.to_numeric(df["bmi"], errors="coerce").fillna(0.0).astype(float)
            df["smoking_status"] = df["smoking_status"].astype(str).fillna("unknown")
            df["stroke"] = pd.to_numeric(df["stroke"], errors="coerce").fillna(0).astype(int)

            records = df.to_dict(orient="records")
            for record in records:
                record["uploaded_by"] = session.get("customer_id")
                record["uploaded_at"] = datetime.utcnow()
            if records:
                stroke_collection.insert_many(records)
            flash(f"Successfully uploaded {len(records)} records.", "success")
            try:
                log_action("UPLOAD_DATA", session.get("customer_id"), {"record_count": len(records)})
            except Exception:
                pass
            return redirect(url_for("admindashboard"))
        except Exception as e:
            flash(f"Error processing file: {str(e)}", "danger")
            return redirect(request.url)
    return render_template("/ad_upload.html")

# Admin view patients
@app.route("/ad_patients")
@admin_required
def admin_view_patients():
    data = list(stroke_collection.find())
    return render_template("/ad_patients.html", records=data)


# Run app
if __name__ == "__main__":
    bootstrap_once()
    app.run(host="0.0.0.0", port=5069, debug=False)





