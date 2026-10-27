"""
Kiosk routes - Register (1.1) and Time In (1.2), narratives Version 1.1.

Flow:  /  ->  /verify (face)  ->  /register (details)
          ->  /select-batch  ->  /confirmation

Nothing is saved to the database until the applicant picks a batch.
Until then the face embedding and typed details live in the session, so
an abandoned registration leaves no record behind.
"""
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Applicant, ExamBatch, Attendance
from app.services import face_service
from app.utils.validators import is_valid_contact_number, is_valid_email

EARLY_GRACE_MINUTES = 15

kiosk_bp = Blueprint('kiosk', __name__)

# Session keys used while a registration is in progress
_PENDING_KEYS = ('face_embedding', 'form')


def _clear_pending():
    for key in _PENDING_KEYS:
        session.pop(key, None)


def _spoken_time(moment):
    """'9:00 AM today' when it is today, otherwise '9:00 AM, Oct 28, 2026'."""
    clock = moment.strftime('%I:%M %p').lstrip('0')
    if moment.date() == datetime.now().date():
        return f"{clock} today"
    return f"{clock}, {moment.strftime('%b %d, %Y')}"


def _email_already_registered(email):
    """Case-insensitive check: one applicant per email address."""
    return Applicant.query.filter(
        db.func.lower(Applicant.email) == email.strip().lower()
    ).first() is not None


def _contact_already_registered(contact_number):
    """One applicant per mobile number."""
    return Applicant.query.filter(
        Applicant.contact_number == contact_number.strip()
    ).first() is not None


def _read_face(photo_data):
    """Turn the posted photo into an encoding, or explain why we can't.

    The Capture button is already disabled in the browser until a face is
    visible; this is the server-side safety net. It never raises: a missing
    field, bad base64 or an unreadable image becomes a message instead of a
    500 error.

    Returns (encoding, problem) - exactly one of them is None.
    """
    try:
        is_valid, reason = face_service.check_face_quality(photo_data)
        if not is_valid:
            return None, f"We couldn't get a clear photo: {reason}"

        encoding = face_service.encode_face(photo_data)
    except (AttributeError, ValueError, OSError):
        return None, "That photo could not be read. Please try again."

    if encoding is None:
        return None, "We couldn't read your face. Please try again."

    return encoding, None


def _new_registration_number():
    """e.g. REG-2026-A3F9C1 - retried in the (unlikely) event of a collision."""
    while True:
        number = f"REG-{datetime.now().year}-{secrets.token_hex(3).upper()}"
        if not Applicant.query.filter_by(registration_number=number).first():
            return number


def _new_reference_number():
    """e.g. ATT-2026-7B21CE - the attendance receipt number."""
    while True:
        number = f"ATT-{datetime.now().year}-{secrets.token_hex(3).upper()}"
        if not Attendance.query.filter_by(reference_number=number).first():
            return number


MAX_TIME_IN_ATTEMPTS = 3


# --------------------------------------------------------------------------
# Start
# --------------------------------------------------------------------------
@kiosk_bp.route('/')
def home():
    """Kiosk home: Register or Time In. Wipes anything left by the last person."""
    _clear_pending()
    for key in ('applicant_id', 'time_in_attempts',
                'time_in_applicant_id', 'time_in_already'):
        session.pop(key, None)
    return render_template('kiosk/home.html')


# --------------------------------------------------------------------------
# Step 1 - face capture + duplicate check (1.1 Steps 2-4)
# --------------------------------------------------------------------------
@kiosk_bp.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        photo_data = request.form.get('photo_data')

        encoding, problem = _read_face(photo_data)
        if problem:
            flash(problem)
            return redirect(url_for('kiosk.verify'))

        # Duplicate check against EVERY registered applicant
        existing = Applicant.query.all()
        if face_service.find_duplicate(encoding, existing):
            _clear_pending()
            flash("This face is already registered. Duplicate registrations are not allowed.")
            return redirect(url_for('kiosk.verify'))

        # Keep the embedding (not the photo) until the record is saved.
        # Rounded to keep the session cookie comfortably under the 4 KB limit.
        session['face_embedding'] = [round(float(x), 5) for x in encoding]
        return redirect(url_for('kiosk.register'))

    return render_template('kiosk/verify.html')


# --------------------------------------------------------------------------
# Step 2 - personal details (1.1 Steps 5-6)
# --------------------------------------------------------------------------
@kiosk_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'face_embedding' not in session:
        return redirect(url_for('kiosk.verify'))

    form = session.get('form', {})

    if request.method == 'POST':
        form = {
            'first_name': request.form.get('first_name', '').strip(),
            'middle_name': request.form.get('middle_name', '').strip(),
            'last_name': request.form.get('last_name', '').strip(),
            'suffix': request.form.get('suffix', '').strip(),
            'contact_number': request.form.get('contact_number', '').strip(),
            'email': request.form.get('email', '').strip(),
            'address': request.form.get('address', '').strip(),
        }

        required = ('first_name', 'last_name', 'contact_number', 'email', 'address')
        if any(not form[f] for f in required):
            flash("Please fill in all required fields.")
        elif not is_valid_contact_number(form['contact_number']):
            flash("Please enter a valid contact number in 09XXXXXXXXX format.")
        elif not is_valid_email(form['email']):
            flash("Please enter a valid email address.")
        else:
            # Both uniqueness checks run, so the applicant is told about
            # every duplicate at once instead of fixing them one per submit.
            taken = []
            if _email_already_registered(form['email']):
                taken.append('email address')
            if _contact_already_registered(form['contact_number']):
                taken.append('contact number')

            if len(taken) == 1:
                flash(f"That {taken[0]} is already registered. Please use a different one.")
            elif taken:
                flash(f"That {' and '.join(taken)} are already registered. "
                      "Please use different ones.")
            else:
                session['form'] = form
                return redirect(url_for('kiosk.select_batch'))

    return render_template('kiosk/register.html', form=form)


# --------------------------------------------------------------------------
# Step 3 - choose a batch, reserve the seat, save the record (1.1 Steps 7-10)
# --------------------------------------------------------------------------
@kiosk_bp.route('/select-batch', methods=['GET', 'POST'])
def select_batch():
    if 'face_embedding' not in session:
        return redirect(url_for('kiosk.verify'))
    if 'form' not in session:
        return redirect(url_for('kiosk.register'))

    if request.method == 'POST':
        batch_id = request.form.get('exam_batch_id', type=int)

        # Lock the batch row so two kiosks can't take the last seat at once,
        # then re-check capacity (Step 9).
        batch = (ExamBatch.query.filter_by(id=batch_id)
                 .with_for_update().first())
        if batch is None or not batch.is_open:
            db.session.rollback()
            flash("That batch is no longer available. Please choose another.")
            return redirect(url_for('kiosk.select_batch'))

        form = session['form']
        applicant = Applicant(
            registration_number=_new_registration_number(),
            first_name=form['first_name'],
            middle_name=form['middle_name'] or None,
            last_name=form['last_name'],
            suffix=form['suffix'] or None,
            contact_number=form['contact_number'],
            email=form['email'],
            address=form['address'],
            face_embedding=session['face_embedding'],
            exam_batch_id=batch.id,
        )
        db.session.add(applicant)
        try:
            db.session.commit()
        except IntegrityError:
            # The database also enforces one applicant per email / number, so
            # two kiosks saving the same person at once can still collide.
            db.session.rollback()
            _clear_pending()
            flash("That email or contact number was just registered. Please start again.", 'error')
            return redirect(url_for('kiosk.home'))

        _clear_pending()
        session['applicant_id'] = applicant.id
        return redirect(url_for('kiosk.confirmation'))

    batches = (ExamBatch.query
               .order_by(ExamBatch.exam_date, ExamBatch.start_time).all())
    open_batches = [b for b in batches if b.is_open]
    return render_template('kiosk/select_batch.html', batches=open_batches)


# --------------------------------------------------------------------------
# Step 4 - confirmation (1.1 Step 11)
# --------------------------------------------------------------------------
@kiosk_bp.route('/confirmation')
def confirmation():
    applicant_id = session.get('applicant_id')
    if not applicant_id:
        return redirect(url_for('kiosk.verify'))

    applicant = db.session.get(Applicant, applicant_id)
    if applicant is None:
        return redirect(url_for('kiosk.verify'))
    return render_template('kiosk/confirmation.html', applicant=applicant)


# ==========================================================================
# TIME IN (1.2) - the applicant is identified from the face alone
# ==========================================================================
@kiosk_bp.route('/time-in', methods=['GET', 'POST'])
def time_in():
    if request.method == 'POST':
        photo_data = request.form.get('photo_data')

        encoding, problem = _read_face(photo_data)
        if problem:
            flash(problem)
            return redirect(url_for('kiosk.time_in'))

        # Step 4: search all registered faces for the best match
        match = face_service.find_match(encoding, Applicant.query.all())

        if not match:
            attempts = session.get('time_in_attempts', 0) + 1
            if attempts >= MAX_TIME_IN_ATTEMPTS:
                # After 3 unsuccessful tries, stop guessing and send them to register.
                session.pop('time_in_attempts', None)
                return render_template('kiosk/face_not_recognized.html')
            session['time_in_attempts'] = attempts
            flash(f"We couldn't identify you. Please try again "
                  f"(attempt {attempts} of {MAX_TIME_IN_ATTEMPTS}).")
            return redirect(url_for('kiosk.time_in'))

        session.pop('time_in_attempts', None)

        # Step 5: already timed in? Show the earlier time-in, record nothing new.
        if match.attendance is not None:
            session['time_in_applicant_id'] = match.id
            session['time_in_already'] = True
            return redirect(url_for('kiosk.time_in_result'))

         # Time In window: from EARLY_GRACE_MINUTES before the batch starts
        # until the batch end time. Outside it, nothing is recorded.
        batch = match.exam_batch
        opens_at = (datetime.combine(batch.exam_date, batch.start_time)
                    - timedelta(minutes=EARLY_GRACE_MINUTES))
        closes_at = datetime.combine(batch.exam_date, batch.end_time)
        now = datetime.now()

        if now < opens_at:
            return render_template(
                'kiosk/time_in_window.html',
                tone='warning',
                heading='Time In Is Not Open Yet',
                message=("Your exam batch has not started. Time In opens at "
                         f"{_spoken_time(opens_at)}. Please come back then."),
            )

        if now > closes_at:
            return render_template(
                'kiosk/time_in_window.html',
                tone='alert',
                heading='Time In Has Closed',
                message=("Time In for your exam batch closed at "
                         f"{_spoken_time(closes_at)}."),
            )

        # Arriving after the start is still Present: there is no "Late" state.
        record = Attendance(
            applicant_id=match.id,
            timed_in_at=datetime.now(),
            status='Present',
            reference_number=_new_reference_number(),
        )
        db.session.add(record)
        try:
            db.session.commit()
        except IntegrityError:
            # Two kiosks timed the same person in at once - the unique
            # constraint kept it to one record.
            db.session.rollback()
            session['time_in_already'] = True
        else:
            session['time_in_already'] = False

        session['time_in_applicant_id'] = match.id
        return redirect(url_for('kiosk.time_in_result'))

    return render_template('kiosk/time_in.html')


@kiosk_bp.route('/time-in/result')
def time_in_result():
    applicant_id = session.get('time_in_applicant_id')
    if not applicant_id:
        return redirect(url_for('kiosk.home'))

    applicant = db.session.get(Applicant, applicant_id)
    if applicant is None or applicant.attendance is None:
        return redirect(url_for('kiosk.home'))

    return render_template(
        'kiosk/time_in_result.html',
        applicant=applicant,
        record=applicant.attendance,
        already=session.get('time_in_already', False),
    )