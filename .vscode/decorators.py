

from functools import wraps
from flask import session, redirect, url_for, flash
from services_admin import is_admin


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

