from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app.models import Admin

# 2.1 Admin Login - handles logging in and logging out.
auth_bp = Blueprint('admin_auth', __name__)


@auth_bp.route('/')
def index():
    """Trigger: 'Admin opens the admin panel.' Logged in -> dashboard, otherwise
    @login_required on the dashboard sends them to the login page."""
    return redirect(url_for('admin.dashboard'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Already signed in - no need to show the form again
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        admin = Admin.query.filter_by(username=username).first() if username and password else None

        # Same message for a wrong username or a wrong password,
        # so the page never reveals which usernames exist.
        if admin and check_password_hash(admin.password_hash, password):
            login_user(admin)
            return redirect(url_for('admin.dashboard'))

        flash('Invalid username or password.')

    return render_template('admin/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin_auth.login'))