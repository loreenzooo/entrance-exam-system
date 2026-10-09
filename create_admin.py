from getpass import getpass
from werkzeug.security import generate_password_hash

from run import app as flask_app
from app.extensions import db
from app.models import Admin

print("Admin columns:", sorted(c.name for c in Admin.__table__.columns))

username = input("Admin username: ").strip()
password = getpass("Admin password: ")

with flask_app.app_context():
    if Admin.query.filter_by(username=username).first():
        print("That admin already exists.")
    else:
        admin = Admin(
            username=username,
            password_hash=generate_password_hash(password),
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Created admin '{username}' (id={admin.id})")