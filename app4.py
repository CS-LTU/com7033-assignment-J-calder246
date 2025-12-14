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
        customer_id = request.form.get("customer_id", "").strip()
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
        confirm_new_password = request.form.get("confirm_password", "")
        

        
        try:
            if new_password:
                if len(new_password) < 8:
                    flash("Password must be at least 8 characters long", "danger")
                    return redirect(url_for("profile"))
                if new_password != confirm_new_password:
                    flash("passwords must match", "danger")
                    return redirect(url_for("profile"))
                pw_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                cur.execute("UPDATE users SET username = ?, password_hash = ? WHERE customer_id = ?", (username,  pw_hash, uid))
            else:
                cur.execute("UPDATE users SET username = ?, WHERE customer_id = ?", (username, ))
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

    cur.execute("SELECT rowid AS id, username, customer_id FROM users WHERE customer_id = ?", (uid,))
    user = cur.fetchone()
    conn.close()
    return render_template("profile.html", user=user)

# -------------------------
# patientdata - Link for users to view their own data
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


@app.route("/contact")
def contact():
    return render_template("contact.html")


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
def ad_patients():
    #gets all data from strokedata collection
    docs = list(stroke_collection.find())
   
    for doc in docs:
        doc['_id'] = str(doc['_id'])  #converts objectid to string not regular id
    if docs:
        df = pd.DataFrame(docs).head(5)
        preview_table = df.to_html(classes='data' ' table-striped', index=False)
        return render_template('ad_patients.html', records=docs, preview_table=preview_table)
    
    
#__________________
#DELETE USER ()


# Admin delete route with parameter in URL
@app.route("/delete/<customer_id>", methods=["POST"])
@admin_required
def delete_user(customer_id):
    # prevent admin deleting themselves
    admin_cid = session.get("customer_id")
    if customer_id == admin_cid:
        flash("You cannot delete your own admin account.", "danger")
        return redirect(url_for("ad_patients"))
    try:
        cur.execute("SELECT customer_id FROM users WHERE customer_id = ?", (customer_id,))
        row = cur.fetchone()
        if row:
            cur.execute("DELETE FROM users WHERE customer_id = ?", (customer_id,))
            cur.execute("DELETE FROM admins WHERE customer_id = ?", (customer_id,))
            conn.commit()
            conn.close()
            # delete any matching Mongo records by customer_id
            try:
                if stroke_collection is not None:
                    stroke_collection.delete_many({"customer_id": customer_id})
            except Exception:
                pass
            flash("User account and related records deleted", "success")
            try:
                log_action("DELETE_USER", admin_cid, {"deleted_customer_id": customer_id})
            except Exception:
                pass
            return redirect(url_for("ad_patients"))
    except Exception:
        # ensure connection closed on error
        try:
            conn.close()
        except Exception:
            pass

    # If not found in users table, maybe it's a Mongo _id
        try:
            oid = ObjectId(customer_id)
            doc = None
            doc = stroke_collection.find_one({"_id": oid}) #finds objectis from mongo
            if doc:
                # if document contains a customer_id, it'll remove corresponding sqlite user
                doc_cid = doc.get("id") #finds the short id from mongo (ie: 1657) that corresponds to the objectid found above
                if doc_cid:
                    try:
                        conn = get_db()
                        cur = conn.cursor()
                        cur.execute("DELETE FROM users WHERE customer_id = ?", (doc_cid,)) #finds short id in sqlite (where it is stored as customer_id) and deletes it
                        cur.execute("DELETE FROM admins WHERE customer_id = ?", (doc_cid,))
                        conn.commit()
                        conn.close()
                    except Exception:
                        pass
                try:
                    stroke_collection.delete_one({"_id": oid}) #deletes dataset in mongoDB
                except Exception:
                    pass
                flash("Patient record deleted", "success")
                try:
                    log_action("DELETE_RECORD", admin_cid, {"deleted_record_id": customer_id}) #logs deletion
                except Exception:
                    pass
                return redirect(url_for("ad_patients"))
        except Exception:
            pass                              
                                      
    '''
    try:
        stroke_collection.delete_one({"_id": ObjectId(_id)})
        flash("User deleted", "success")
    except Exception:
        flash("Error deleting user.", "danger")
    return redirect(url_for("admindashboard"))
    '''


    

#__________________
#UPDATE USER
#__________________

@app.route("/ad_update/<_id>", methods=["GET"])
@admin_required
def update_user(_id):
    doc = stroke_collection.find_one({"_id": ObjectId(_id)})  #bases update of objectid (_id)
    
    if not doc:
        flash("User not found.", "danger")
        return redirect(url_for("ad_patients"))
    doc['_id'] = str(doc['_id'])
    return render_template("ad_update.html", record=doc)


#____________
#Update
#____________
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
        "ever_married" : (ever_married),
        "work_type" : (work_type),
        "Residence_type" : (Residence_type),
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
        "id" : str(id),
        "gender" : gender,
        "age" : str(age),
        "hypertension" : str(hypertension),
        "heart_disease" : str(heart_disease),
        "ever_married" : str(ever_married),
        "work_type" : str(work_type),
        "Residence_type" : str(Residence_type),
        "avg_glucose_level" : float(avg_glucose_level),
        "bmi" : float(bmi),
        "smoking_status": str(smoking_status),
        "stroke" : str(stroke)
        }
    #inserting
    stroke_collection.insert_one(updated_data)
    flash("New user created successfully.", "success")
    return redirect(url_for('admindashboard'))



# Admin view patients
@app.route("/ad_patients")
@admin_required
def admin_view_patients():
    data = list(stroke_collection.find())
    return render_template("/ad_patients.html", records=data)

