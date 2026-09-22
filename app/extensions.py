from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# These are created here WITHOUT an app attached yet.
# They get connected to the real app inside create_app() in app/__init__.py.
# This avoids circular imports between models.py and route files.

db = SQLAlchemy()

login_manager = LoginManager()
login_manager.login_view = 'admin_auth.login'  # where to redirect if not logged in
login_manager.login_message = 'Please log in to access the admin dashboard.'