from flask import Flask, render_template, request, redirect, url_for
from IPython.display import display, Javascript
#^^importing flask and Ipython modules
app = Flask(__name__) #initialises app
#storing registered users
users = []
@app.route('/')
def home():
    return render_template('home.html')

#route to contact
@app.route('contact')
def contact():
    return render_template('contact.html')

#route to registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_id = request.form['id']
        email = request.form['email']
        password = request.form['password']
        #storing user details in a dictionary
        user = {
            'id': user_id,
            'email': email,
            'password': password
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
#adds fuctionto run flask app
def run_flask():
    app.run(host='0.0.0.0' , port=5000)
#start app
run_flask()
