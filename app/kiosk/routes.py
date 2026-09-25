from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.extensions import db
from app.models import Applicant, Program, ExamBatch
from app.services.batch_service import refresh_batch_status
from app.services import face_service, attendance_service, audit_service

kiosk_bp = Blueprint('kiosk', __name__)


@kiosk_bp.route('/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        age = request.form.get('age')
        contact_number = request.form.get('contact_number')
        program_id = request.form.get('program_id')

        new_applicant = Applicant(
            full_name=full_name,
            age=int(age),
            contact_number=contact_number,
            program_id=int(program_id)
        )
        db.session.add(new_applicant)
        db.session.commit()

        session['applicant_id'] = new_applicant.id
        return redirect(url_for('kiosk.select_batch'))

    programs = Program.query.all()
    return render_template('kiosk/register.html', programs=programs)


@kiosk_bp.route('/select-batch', methods=['GET', 'POST'])
def select_batch():
    applicant_id = session.get('applicant_id')
    if not applicant_id:
        return redirect(url_for('kiosk.register'))

    applicant = Applicant.query.get_or_404(applicant_id)

    if request.method == 'POST':
        batch_id = request.form.get('exam_batch_id')
        applicant.exam_batch_id = int(batch_id)
        db.session.commit()
        return redirect(url_for('kiosk.verify'))

    all_batches = ExamBatch.query.order_by(ExamBatch.start_time).all()
    for batch in all_batches:
        refresh_batch_status(batch)
    db.session.commit()

    open_batches = [b for b in all_batches if b.status == 'open']
    return render_template('kiosk/select_batch.html', batches=open_batches, applicant=applicant)


@kiosk_bp.route('/verify', methods=['GET', 'POST'])
def verify():
    applicant_id = session.get('applicant_id')
    if not applicant_id:
        return redirect(url_for('kiosk.register'))

    applicant = Applicant.query.get_or_404(applicant_id)

    if request.method == 'POST':
        photo_data = request.form.get('photo_data')

        # 1. Quality check (currently a placeholder - always passes)
        is_valid, reason = face_service.check_face_quality(photo_data)
        if not is_valid:
            flash(f"Capture failed: {reason}")
            return redirect(url_for('kiosk.verify'))

        # 2. Encode the face (currently a placeholder - fake numbers)
        encoding = face_service.encode_face(photo_data)

        # 3. Duplicate check against every OTHER applicant
        other_applicants = Applicant.query.filter(Applicant.id != applicant.id).all()
        duplicate = face_service.find_duplicate(encoding, other_applicants)
        if duplicate:
            flash("You are already registered in our system. Duplicate registrations are not allowed.")
            return redirect(url_for('kiosk.register'))

        applicant.face_encoding = encoding
        db.session.commit()

        # 4. Record attendance (real logic - checks batch window, generates ref number)
        try:
            attendance_service.record_attendance(applicant)
        except ValueError as e:
            flash(str(e))
            return redirect(url_for('kiosk.select_batch'))

        # 5. Audit log entry
        audit_service.log_action(
            actor='system',
            action='Attendance recorded',
            details=f"Applicant #{applicant.id} ({applicant.full_name}), ref {applicant.reference_number}"
        )

        return redirect(url_for('kiosk.confirmation'))

    return render_template('kiosk/verify.html', applicant=applicant)


@kiosk_bp.route('/confirmation')
def confirmation():
    applicant_id = session.get('applicant_id')
    if not applicant_id:
        return redirect(url_for('kiosk.register'))

    applicant = Applicant.query.get_or_404(applicant_id)
    return render_template('kiosk/confirmation.html', applicant=applicant)