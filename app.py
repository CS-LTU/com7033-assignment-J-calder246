"""
IMPORTING LIBRARIES
"""



from IPython.display import display, Javascript
from flask import Flask, request, redirect, render_template, flash, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from pymongo import MongoClient;
from bson.objectid import ObjectId;
import pandas as pd;

"""
AUTHENTICATION WITH SQLite
"""
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

app = Flask(__name__) #initialises app
app.config['SECRET_KEY'] = 'your_secret_key' #sets secret key for session management]
#storing registered users
users = []

"""
ROUTES
"""
@app.route('/')
def home():
    return render_template('home.html')

#route to contact
@app.route('/contact')
def contact():
    return render_template('contact.html')
"""
REGISTRATION AND LOGIN
"""
#route to registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_id = request.form['id'].strip()

        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        #storing user details in a dictionary
        user = {
            'id': user_id,
            'email': email,
            'password': password,
            'role': role
        }
        users.append(user) #adding new user to list of users
        #displaying alert message using javascript
        display(Javascript('alert("Registration successful!")'))
        return redirect(url_for('home'))
    return render_template('registration.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        #checking user credentials
        for user in users:
            if user['email'] == email and user['password'] == password:
                display(Javascript('alert("Login successful!")'))
                return redirect(url_for('home'))
        display(Javascript('alert("Invalid email or password.")'))
    return render_template('login.html')


"""
INTEGRATING MONGODB
"""
# Initialize MongoDB client
client = MongoClient('mongodb+srv://2511607_db_user:8eOYxezbnZPcBiHh@stroke-dataset.w6p63mq.mongodb.net/')

# Getting server info
server_info = client.server_info()
mongo_version = server_info['version']
print(f'MongoDB Version: {mongo_version}')

# Access database and collection
db = client['medicaldata']
collection = db['strokedata']

# CRUD Operations
def create_user(_id, id, gender, age, hypertension, heart_disease, ever_married, work_type, Residence_type, avg_glucose_level, bmi, smoking_status, stroke):
    new_doc = {
        "_id": _id, "id": id, "gender": gender, "age": age,
        "hypertension": hypertension, "heart_disease": heart_disease,
        "ever_married": ever_married, "work_type": work_type,
        "Residence_type": Residence_type, "avg_glucose_level": avg_glucose_level,
        "bmi": bmi, "smoking_status": smoking_status, "stroke": stroke
    }
    result = collection.insert_one(new_doc)
    print(f"[CREATE] Inserted document with _id={result.inserted_id}")
    return result.inserted_id

def read_strokedata(filter_query=None):
    if filter_query is None:
        filter_query = {}
    docs = list(collection.find(filter_query))
    print(f"[READ] Found {len(docs)} documents matching {filter_query}:")
    for d in docs:
        print(d)
    return docs

def update_strokedata(document_id, new_gender=None, new_age=None, new_hypertension=None, new_heart_disease=None, new_ever_married=None, new_work_type=None, new_Residence_type=None, new_avg_glucose_level=None, new_bmi=None, new_smoking_status=None, new_stroke=None):
    update_fields = {}
    if new_gender is not None:
        update_fields["gender"] = new_gender
    if new_age is not None:
        update_fields["age"] = new_age
    if new_hypertension is not None:
        update_fields["hypertension"] = new_hypertension
    if new_heart_disease is not None:
        update_fields["heart_disease"] = new_heart_disease
    if new_ever_married is not None:
        update_fields["ever_married"] = new_ever_married
    if new_work_type is not None:
        update_fields["work_type"] = new_work_type
    if new_Residence_type is not None:
        update_fields["Residence_type"] = new_Residence_type
    if new_avg_glucose_level is not None:
        update_fields["avg_glucose_level"] = new_avg_glucose_level
    if new_bmi is not None:
        update_fields["bmi"] = new_bmi
    if new_smoking_status is not None:
        update_fields["smoking_status"] = new_smoking_status
    if new_stroke is not None:
        update_fields["stroke"] = new_stroke
    
    result = collection.update_one({"_id": ObjectId(document_id)}, {"$set": update_fields})
    print(f"[UPDATE] Matched {result.matched_count}, Modified {result.modified_count}")

def destroy_patient(document_id):
    result = collection.delete_one({"_id": ObjectId(document_id)})
    print(f"[DELETE] Deleted {result.deleted_count} document with _id {document_id}")

# Flask app
app = Flask(__name__)

@app.route('/')
def index():
    collections = db.list_collection_names()
    data_dict = {}
    for collection_name in collections:
        collection = db[collection_name]
        data_list = list(collection.find())
        if data_list:
            df = pd.DataFrame(data_list)
            data_dict[collection_name] = df.head().to_html(classes='data', headers='true')
        else:
            data_dict[collection_name] = "no data in this collection"
    return render_template('index.html', data=data_dict)

if __name__ == "__main__":
    app.run(debug=False)

    """
    RUN APP
    """
#adds fuctionto run flask app
def run_flask():
    app.run(host='0.0.0.0' , port=5000)
#start app
run_flask()
