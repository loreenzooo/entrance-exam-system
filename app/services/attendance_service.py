from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Applicant, ExamBatch, Attendance


def mark_absent_for_ended_batches():
    """Every applicant of an ended batch with no attendance record becomes Absent.
    Safe to call repeatedly: it only adds rows that are missing."""
    ended_ids = [b.id for b in ExamBatch.query.all() if b.has_ended]
    if not ended_ids:
        return

    missing = (Applicant.query
               .outerjoin(Attendance, Attendance.applicant_id == Applicant.id)
               .filter(Applicant.exam_batch_id.in_(ended_ids),
                       Attendance.id.is_(None))
               .all())
    if not missing:
        return

    for applicant in missing:
        db.session.add(Attendance(applicant_id=applicant.id, status='Absent'))
    try:
        db.session.commit()
    except IntegrityError:
        # Another request created some of them at the same moment.
        db.session.rollback()