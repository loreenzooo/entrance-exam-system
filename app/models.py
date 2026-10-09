"""
Schema for the Entrance Exam Face Recognition Attendance System.
Matches the use case narratives, Version 1.1 (October 6, 2026):
  1.1 Register, 1.2 Time In, 2.1 Admin Login,
  2.2 Manage Exam Schedule, 2.3 View Attendance.
"""
from datetime import datetime, date, time

from flask_login import UserMixin
from sqlalchemy import CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB

from app.extensions import db


# --------------------------------------------------------------------------
# Admin  (2.1 Admin Login)
# --------------------------------------------------------------------------
class Admin(db.Model, UserMixin):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)  # salted hash, never plain text
    full_name = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    exam_batches = db.relationship('ExamBatch', backref='created_by_admin', lazy=True)

# --------------------------------------------------------------------------
# Exam batch  (2.2 Manage Exam Schedule)
# The automatic batch ID is the primary key.
# --------------------------------------------------------------------------
class ExamBatch(db.Model):
    __tablename__ = 'exam_batches'
    __table_args__ = (
        CheckConstraint('capacity >= 1', name='ck_batch_capacity_min_1'),
        CheckConstraint('end_time > start_time', name='ck_batch_end_after_start'),
    )

    id = db.Column(db.Integer, primary_key=True)          # automatic batch ID
    exam_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    building = db.Column(db.String(120), nullable=False)
    room = db.Column(db.String(60), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)

    created_by = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # No cascade on purpose: PostgreSQL itself refuses to delete a batch that
    # still has applicants (2.2: delete only if no applicant is assigned).
    applicants = db.relationship('Applicant', backref='exam_batch', lazy=True)

    # ---- computed, so they can never go stale ----
    @property
    def reserved_seats(self):
        return len(self.applicants)

    @property
    def is_full(self):
        return self.reserved_seats >= self.capacity

    @property
    def is_ongoing(self):
        """True while the current time is within start and end time (2.2)."""
        now = datetime.now()
        return (self.exam_date == now.date()
                and self.start_time <= now.time() <= self.end_time)

    @property
    def has_ended(self):
        now = datetime.now()
        return (self.exam_date < now.date()
                or (self.exam_date == now.date() and now.time() > self.end_time))

    @property
    def is_open(self):
        """Shown at registration: not full and not already over (1.1 Step 7)."""
        return not self.is_full and not self.has_ended

    @property
    def is_editable(self):
        """2.2: update/delete only if not ongoing and no applicant assigned."""
        return not self.is_ongoing and self.reserved_seats == 0


# --------------------------------------------------------------------------
# Applicant  (1.1 Register)
# --------------------------------------------------------------------------
class Applicant(db.Model):
    __tablename__ = 'applicants'

    id = db.Column(db.Integer, primary_key=True)
    registration_number = db.Column(db.String(30), unique=True, nullable=False)

    first_name = db.Column(db.String(80), nullable=False)
    middle_name = db.Column(db.String(80), nullable=True)    # optional
    last_name = db.Column(db.String(80), nullable=False)
    suffix = db.Column(db.String(20), nullable=True)         # optional
    contact_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    address = db.Column(db.String(255), nullable=False)

    # Face embedding only, never the photo. Duplicate check (1.1 Step 4)
    # compares a new embedding against these.
    face_embedding = db.Column(JSONB, nullable=False)
    biometric_consent_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # 1.1 Step 5

    # Reserved seat (1.1 Step 9)
    exam_batch_id = db.Column(db.Integer, db.ForeignKey('exam_batches.id'), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

    attendance = db.relationship('Attendance', backref='applicant', uselist=False, lazy=True)

    @property
    def face_encoding(self):
        """Alias so existing face_service code (which reads .face_encoding) keeps working."""
        return self.face_embedding

    @property
    def full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name, self.suffix]
        return ' '.join(p for p in parts if p)


# --------------------------------------------------------------------------
# Attendance  (1.2 Time In, 2.3 View Attendance)
# --------------------------------------------------------------------------
class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)

    # unique=True: an applicant can only ever have ONE attendance record,
    # which is the "has not already timed in" rule (1.2 Step 5).
    applicant_id = db.Column(db.Integer, db.ForeignKey('applicants.id'),
                             nullable=False, unique=True)

    timed_in_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='Present')  # always Present in v1.1
    reference_number = db.Column(db.String(30), unique=True, nullable=False)

    # The batch is reached through the applicant: attendance.applicant.exam_batch