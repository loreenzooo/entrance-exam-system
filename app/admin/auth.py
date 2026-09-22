from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from app.models import Admin

# This blueprint only handles logging in and logging out.
auth_bp = Blueprint('admin_auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # GET request = just show the login form
    # POST request = the form was submitted, check the credentials
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        admin = Admin.query.filter_by(username=username).first()

        # check_password_hash compares the typed password against
        # the hashed one stored in the database - never compare
        # plain text passwords directly.
        if admin and check_password_hash(admin.password_hash, password):
            login_user(admin)  # this creates the logged-in session
            return redirect(url_for('admin.dashboard'))

        flash('Invalid username or password.')

    return render_template('admin/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin_auth.login'))