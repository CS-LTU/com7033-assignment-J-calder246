#authentication route


from flask import Blueprint, render_template, redirect, url_for, flash, request;
from werkzeug.security import generate_password_hash, check_password_hash;
from flask_login import login_user, logout_user, login_required, current_user;
from app2 import db ;
from dbmodels.user_model import User;
from forms import RegistrationForm, LoginForm;  

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for)
            return redirect(url_for('user.dashboard'))
        else:
            flash('Login failed, incorrect username and/or password.', 'danger')
    return render_template('login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
            form = RegistrationForm()
            if form.validate_on_submit():
                   if current_user.is_admin:
                         is_admin = form.is_admin.data
                   else:
                         is_admin = False
            hashed_password = generate_password_hash(form.password.data, method='sha512')
            new_user = User(username=form.username.data, password=hashed_password, is_admin=is_admin)
            db.session.add(new_user)
            db.session.commit()
            flash('account created', 'success')
            return redirect(url_for('auth.login'))
            return render_template('register.html', form=form)
