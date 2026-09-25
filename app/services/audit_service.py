from datetime import datetime
from app.extensions import db
from app.models import AuditLog


def log_action(actor, action, details=None):
    """
    Call this from anywhere in the app whenever something worth
    tracking happens: registrations, verifications, admin logins,
    batch edits, deletions, etc.

    actor: who did it, e.g. current_user.username or 'system'
    action: short description, e.g. 'Attendance recorded'
    details: optional extra info, e.g. the applicant's reference number
    """
    entry = AuditLog(
        actor=actor,
        action=action,
        details=details,
        timestamp=datetime.utcnow()
    )
    db.session.add(entry)
    db.session.commit()
    return entry