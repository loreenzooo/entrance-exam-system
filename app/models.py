from datetime import datetime
from flask_login import UserMixin
from app.extensions import db


class Admin(db.Model, UserMixin):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    exam_batches = db.relationship('ExamBatch', backref='created_by_admin', lazy=True)


class Program(db.Model):
    __tablename__ = 'programs'

    id = db.Column(db.Integer, primary_key=True)
    program_name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    applicants = db.relationship('Applicant', backref='program', lazy=True)


class ExamBatch(db.Model):
    __tablename__ = 'exam_batches'

    id = db.Column(db.Integer, primary_key=True)
    batch_name = db.Column(db.String(120), nullable=False)
    exam_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    venue = db.Column(db.String(120), nullable=True)
    # scheduled / open / full / closed / ongoing
    status = db.Column(db.String(20), default='scheduled')
    created_by = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applicants = db.relationship('Applicant', backref='exam_batch', lazy=True)
    attendances = db.relationship('Attendance', backref='exam_batch', lazy=True)


class Applicant(db.Model):
    __tablename__ = 'applicants'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey('programs.id'), nullable=False)

    # Numeric face data (128 values from face_recognition), stored as JSON.
    # Never store a raw photo here.
    face_encoding = db.Column(db.JSON, nullable=True)

    reference_number = db.Column(db.String(30), unique=True, nullable=True)
    exam_batch_id = db.Column(db.Integer, db.ForeignKey('exam_batches.id'), nullable=True)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)


class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    applicant_id = db.Column(db.Integer, db.ForeignKey('applicants.id'), nullable=False)
    exam_batch_id = db.Column(db.Integer, db.ForeignKey('exam_batches.id'), nullable=False)
    verified_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='present')  # present / late / absent

    applicant = db.relationship('Applicant', backref='attendance_records', lazy=True)


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    actor = db.Column(db.String(150), nullable=False)   # admin username, or 'system'
    action = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)