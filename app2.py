"""
IMPORTING LIBRARIES
"""

from IPython.display import display, Javascript
from flask import Flask, request, redirect, render_template, url_for
from pymongo import MongoClient;
import pandas as pd;
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

"""
initializing Flask app and secret key
"""
app = Flask(__name__)
app.config['SECRET_KEY'] = 'K09ob4rrySecret' #sets up secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db' #database uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


#INITIALISE sql DATABASE
SQL_db = SQLAlchemy(app)

# Initialize MongoDB client
client = MongoClient('mongodb+srv://2511607_db_user:8eOYxezbnZPcBiHh@stroke-dataset.w6p63mq.mongodb.net/')


    

# Access database and collection
db = client['medicaldata']
collection = db['strokedata']

#longin manager initialise
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app) 

#routes

@app.route('/')
def register():
    return render_template('registration.html')
    #handling user ragistration
    # @app.route('/register', methods=['POST'])
def do_register():
    id = request.form.get("id", "").strip()
    username = request.form.get("email", "").strip()
    password = request.form.get("password", "")

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
