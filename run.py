from flask import Flask
from dotenv import load_dotenv
import os

# Import the 'db' object and your models from the app folder
from app.models import db, Admin, ExamBatch, Applicant, Attendance, AuditLog

# 1. Load the hidden variables from the .env file
load_dotenv()

app = Flask(__name__)

# 2. Configure the PostgreSQL database connection
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 3. Connect the database to the Flask app
db.init_app(app)

# 4. Create the tables based on your models.py blueprints
with app.app_context():
    db.create_all()
    print("✅ Successfully connected to PostgreSQL and created the tables!")

@app.route('/')
def hello():
    return "Database connected and ready!"

if __name__ == '__main__':
    app.run(debug=True)