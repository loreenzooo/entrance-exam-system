from flask import Flask
from dotenv import load_dotenv
import os

# Import the 'db' and 'login_manager' objects from extensions.py
from app.extensions import db, login_manager

# Import your models
from app.models import Admin, ExamBatch, Applicant, Attendance, AuditLog

# 1. Load the hidden variables from the .env file
load_dotenv()

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')

# 2. Configure the PostgreSQL database connection
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  # needed for login sessions + flash messages

# 3. Connect the database and login manager to the Flask app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'admin_auth.login'  # redirect here if not logged in

# 4. Tell Flask-Login how to load the currently logged-in admin
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Admin, int(user_id))

# 5. Register the admin blueprints
from app.admin.auth import auth_bp
from app.admin.routes import admin_bp

app.register_blueprint(auth_bp, url_prefix='/admin')
app.register_blueprint(admin_bp, url_prefix='/admin')

# 6. Register the kiosk blueprint (public, no login - this IS the home page now)
from app.kiosk.routes import kiosk_bp
app.register_blueprint(kiosk_bp)

# 7. Create the tables based on your models.py blueprints
with app.app_context():
    db.create_all()
    print("✅ Successfully connected to PostgreSQL and created the tables!")

if __name__ == '__main__':
    app.run(debug=True)