from app.extensions import db
from app.models import Attendance
from app.utils.reference_number import generate_reference_number
from app.services.batch_service import refresh_batch_status


def record_attendance(applicant):
    """
    Full attendance flow for one applicant:
    1. Check they actually have a batch selected
    2. Refresh + check the batch is still open/ongoing (not closed)
    3. Double-check capacity directly (safety net for near-simultaneous
       confirmations, since refresh_batch_status alone runs slightly
       before this check)
    4. Generate a reference number and attach it to the applicant
    5. Save the Attendance row - this is the moment the slot is
       actually considered "used"

    Raises ValueError with a human-readable message if anything blocks it.
    """
    batch = applicant.exam_batch
    if batch is None:
        raise ValueError("No exam batch has been selected yet.")

    refresh_batch_status(batch)
    db.session.commit()

    if batch.status not in ('open', 'ongoing'):
        raise ValueError(f"This exam batch is currently '{batch.status}' and cannot accept attendance right now.")

    if len(batch.attendances) >= batch.capacity:
        raise ValueError("This exam batch just reached full capacity. Please select a different batch.")

    applicant.reference_number = generate_reference_number()

    attendance = Attendance(
        applicant_id=applicant.id,
        exam_batch_id=batch.id,
        status='present'
    )
    db.session.add(attendance)
    db.session.commit()

    return attendance