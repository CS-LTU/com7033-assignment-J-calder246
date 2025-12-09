#admin route


from flask import Blueprint, render_template
from flask_login import login_required, current_user

 from decorators import admin_required
from dbmodels.user import User

admin_routes_bp = Blueprint('admin_routes', __name__)

#setting route to admin dashboard template
@admin_routes_bp.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html', user=current_user)

@admin_routes.route('/create')
@login_required
@admin_required
def create_user():
    users = User.query.all()
    return render_template('create.html', users=users)

@admin_routes.route('/patients')
@login_required
@admin_required
def read_user():
    users = User.query.all()
    return render_template('patients.html', users=users)

@admin_routes.route('/update')
@login_required
@admin_required
def update_user():
    users = User.query.all()
    return render_template('update.html', users=users)

@admin_routes.route('/delete')
@login_required
@admin_required
def delete_user():
    users = User.query.all()
    return render_template('delete.html', users=users)
