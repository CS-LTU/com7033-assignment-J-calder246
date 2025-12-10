import sqlite3;
from flask import Flask, render_template, request, redirect, flash;
import pandas as pd;
import pymongo;
import bcrypt;

#initialise flask
app = Flask(__name__)
app.secret_key = 'Buglady458'


#MongoDB setup
client = pymongo.MongoClient("mongodb+srv://2511607_db_user:8eOYxezbnZPcBiHh@stroke-dataset.w6p63mq.mongodb.net/")
db = client['medicaldata']
collection = db['strokedata']

#sqlitesetup
def init_sqlite_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       username TEXT NOT NULL UNIQUE,
                       customer_id TEXT NOT NULL UNIQUE,
                       password TEXT NOT NULL)''')   #maybe add admin role if I have to
    conn.commit()
    conn.close()

init_sqlite_db()

"""
ROUTE FOR USERS 
"""

#route to homepage
@app.route('/')
def home():
    return render_template('home.html')

#route to registration page
@app.route('/register', methods=['GET', 'POST']
)
def register():
    if request.method == 'POST':
        id = request.form['id']
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (id, username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect('/login')
        except sqlite3.IntegrityError:
            flash('ID already exists. Please choose a different one. or login', 'error')
        finally:
            conn.close()
    return render_template('register.html')

#route to display register data (excempting password)
@app.route('/index')
def index():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users")
    users = cursor.fetchall()
    conn.close()
    return render_template('index.html', users=users)

#route to display info for specific user
@app.route('/patientview', methods=['GET', 'POST'])
def patientview():
    if request.method == 'POST':
        user_id = request.form['id']
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        if user:
            return render_template('patientview.html', user=user)
        else:
            flash('No matching id', 'danger')
    return render_template('patientview.html')

if __name__ == "__main__":
    app.run(debug=False)




"""Admin and permisssions section
"""

import os
import sqlite3
from datetime import datetime #used for timestamps
from functools import wraps #for writing decorators correctly
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import pandas as pd
import pymongo
import bcrypt


#configuration
BASE-DIR = os.getcwd() #current directory
DB_PATH = os.path.join(BASE-DIR, "users.db") #path to users.db
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads") #directory to saved csvs
ALLOWED_EXTENSIONS = {"csv"} #restricts uploads to csv
os.makedirs(UPLOAD_FOLDER, EXIST_OK=tRUE)

APP = fLASK(__NAME__)
app.secret_key = os.environ.get("SECRET_KEY", "change_me_dev_key") #makes secret key



#MongoDB setup
client = pymongo.MongoClient("mongodb+srv://2511607_db_user:8eOYxezbnZPcBiHh@stroke-dataset.w6p63mq.mongodb.net/")
mdb = client['medicaldata']
stroke_collection = mdb["strokedata"]
collection = mdb['logs'] #collection of audit logs

#SQLite helper
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
    #opens users.db connection
def init_sqlite_db():
    conn = get_db()
    cur = conn.cursor
    #table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
    _id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    customer_id TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    )
    """)
    #make username unique
    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_unique
    ON users(username)
    """)
    
    #admin table
    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_admins_username_unique
                ON users(username)
                """)
    #making a table for admins
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins(
                customer_id TEXT PRIMARY KEY
    )
    """)
    conn.commit()
    conn.close()

def is_admin(customer_id str) -> bool:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM admins WHERE customer_id = ?", (customer_id,))
    result = cur.fetchone()
    conn.close()
    return result is not None
#^^ this fuction checks if a customer id exists in the admin table, if true the user has admin permissions


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#^^ checks if uploaded file is a csv
def log_action(action, actor_cid, details=None):
    try:
        logs_collection.insert_one({
            "action": action,
            "actor_customer_id": actor_cid,
            "details": details or {},
            "timestamp": datetime.utcnow(),
        })
    except Exception as e:
        print("Error in logging") #means app won't break if the attempted log fails
    #^^^ function for logging actions
def login_required(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if "customer_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return inner
#^^ code to ensure that a user is logged in by checking is the customer id exists


def admin_required(f):
    @wraps(f)
    def inner(*args, **kwargs):
        cid = session.get("customer_id")
        if not cid:
            flash("please log in first.", "warning!")
            return redirect(url_for("login"))
        if not is_admin(cid):
            flash("Admin access required.", "danger")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return inner
#^^ ensures that admin is an admin and logged in as such. if not logged in --> redirecets to login page. If not admin --> redirects to homepage


"""
BOOTSTRAP LOGIC"""
def bootstrap_once():
if app.config.get("BOOTSTRAPPED"):
    return
init_sqlite_db() #confirms table exists

conn = get_db()
cur = conn.cursor()
cur.execute("SELECT COUNT(*) as admin_count FROM admins")
has_admins = cur.fetchone()["admin_count"] > 0
if not has_admins:
    username = "Applebee"
    customer_id = "admin001"
    pw_hash = bcrypt.hashpw("AdminPass42069".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    
    #inserts admin account
    cur.execute("SELECT 1 FROM users WHERE customer_id = ?", (customer_id))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (username, customer_id, password_hash) VALUES (?, ?, ?)",
            (username, customer_id, pw_hash)
        )
    #nOW GRANTING ADMIN ROLE
    cur.execute("INSERT INTO admins (customer_id) VALUES (?)", (customer_id,))
    conn.commit()
    log_action("CREATED_DEFAULT_ADMIN", customer_id,{})
conn.close()
app.config["BOOTSTRAPPED"] = True

#confirming BOOTSTRAP
@app.before_request
def ensure_bootstrap():
    if not app.config.get("BOOTSTRAPPED"):
        bootstrap_once()

#route to registration page
@app.route('/register', methods=['GET', 'POST']
)


#_____
# PAGE ROUTES
#_____



#registration
def register():
    if request.method == 'POST':
        id = request.form['id']
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (id, username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect('/login')
        except sqlite3.IntegrityError:
            flash('ID already exists. Please choose a different one. or login', 'error')
        finally:
            conn.close()
    return render_template('register.html')

#log in
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"].encode("utf-8")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password, user["password_hash"].encode("utf-8")):
            session["username"] = username
            flash("Login successful!", "success")
            log_action("USER_LOGIN", username, {})
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password.", "danger")
    return render_template("login.html")
#logout
@app.route("/logout")
def logout():
    cid = session.get("customer_id")
    session.clear()
    flash("Successfully logged out.", "info")
    if cid:
        log_action("LOGOUT", cid, {})
    return redirect(url_for("home"))

#route to user data
@app.route("/patientview")
@login_required
def patientview():
    cid = session.get("customer_id")
    try:
        records = list(stroke_collection.find({"customer_id": cid}))
    except Exception:
        records = []
    return render_template("patientview.html", records=records)

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
    for user in USERS
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
    cur.execute("SELECT id FROM users WHERE customer_id = ?", (customer_id)
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

        filename = secure_filename(file.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)

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
        df["work_type"] = pd.to_str(df["work_type"]).fillna("unknown).astype(str)
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
       



