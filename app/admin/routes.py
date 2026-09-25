from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Program, ExamBatch, Applicant, Attendance, AuditLog
from app.services.batch_service import refresh_batch_status, is_batch_editable
from app.services import audit_service

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('admin/dashboard.html')


# ---------- PROGRAMS ----------

@admin_bp.route('/programs', methods=['GET', 'POST'])
@login_required
def programs():
    if request.method == 'POST':
        program_name = request.form.get('program_name')
        description = request.form.get('description')

        new_program = Program(program_name=program_name, description=description)
        db.session.add(new_program)
        db.session.commit()

        audit_service.log_action(current_user.username, 'Added program', program_name)

        return redirect(url_for('admin.programs'))

    all_programs = Program.query.all()
    return render_template('admin/programs.html', programs=all_programs)


@admin_bp.route('/programs/<int:program_id>/delete', methods=['POST'])
@login_required
def delete_program(program_id):
    program = Program.query.get_or_404(program_id)
    program_name = program.program_name

    db.session.delete(program)
    db.session.commit()

    audit_service.log_action(current_user.username, 'Deleted program', program_name)

    return redirect(url_for('admin.programs'))


# ---------- EXAM BATCHES ----------

@admin_bp.route('/batches', methods=['GET', 'POST'])
@login_required
def batches():
    if request.method == 'POST':
        batch_name = request.form.get('batch_name')
        exam_date = datetime.strptime(request.form.get('exam_date'), '%Y-%m-%d').date()
        start_time = datetime.strptime(f"{exam_date} {request.form.get('start_time')}", '%Y-%m-%d %H:%M')
        end_time = datetime.strptime(f"{exam_date} {request.form.get('end_time')}", '%Y-%m-%d %H:%M')
        capacity = int(request.form.get('capacity'))
        venue = request.form.get('venue')

        new_batch = ExamBatch(
            batch_name=batch_name,
            exam_date=exam_date,
            start_time=start_time,
            end_time=end_time,
            capacity=capacity,
            venue=venue,
            status='open',
            created_by=current_user.id
        )
        db.session.add(new_batch)
        db.session.commit()

        audit_service.log_action(current_user.username, 'Created exam batch', batch_name)

        return redirect(url_for('admin.batches'))

    all_batches = ExamBatch.query.order_by(ExamBatch.start_time).all()
    for batch in all_batches:
        refresh_batch_status(batch)
    db.session.commit()

    return render_template('admin/batches.html', batches=all_batches)


@admin_bp.route('/batches/<int:batch_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_batch(batch_id):
    batch = ExamBatch.query.get_or_404(batch_id)
    refresh_batch_status(batch)
    db.session.commit()

    if not is_batch_editable(batch):
        flash('This batch cannot be edited because it is ongoing or already has applicants.')
        return redirect(url_for('admin.batches'))

    if request.method == 'POST':
        batch.batch_name = request.form.get('batch_name')
        batch.exam_date = datetime.strptime(request.form.get('exam_date'), '%Y-%m-%d').date()
        batch.start_time = datetime.strptime(f"{batch.exam_date} {request.form.get('start_time')}", '%Y-%m-%d %H:%M')
        batch.end_time = datetime.strptime(f"{batch.exam_date} {request.form.get('end_time')}", '%Y-%m-%d %H:%M')
        batch.capacity = int(request.form.get('capacity'))
        batch.venue = request.form.get('venue')

        db.session.commit()

        audit_service.log_action(current_user.username, 'Edited exam batch', batch.batch_name)

        return redirect(url_for('admin.batches'))

    return render_template('admin/edit_batch.html', batch=batch)


@admin_bp.route('/batches/<int:batch_id>/delete', methods=['POST'])
@login_required
def delete_batch(batch_id):
    batch = ExamBatch.query.get_or_404(batch_id)
    refresh_batch_status(batch)
    db.session.commit()

    if not is_batch_editable(batch):
        flash('This batch cannot be deleted because it is ongoing or already has applicants.')
        return redirect(url_for('admin.batches'))

    batch_name = batch.batch_name
    db.session.delete(batch)
    db.session.commit()

    audit_service.log_action(current_user.username, 'Deleted exam batch', batch_name)

    return redirect(url_for('admin.batches'))


# ---------- APPLICANTS ----------

@admin_bp.route('/applicants')
@login_required
def applicants():
    search = request.args.get('search', '').strip()
    show_all = request.args.get('show_all') == '1'

    query = Applicant.query

    if not show_all:
        # By default, hide incomplete registrations - people who started
        # but never finished face verification (abandoned, or blocked as
        # a duplicate). Completed ones always have a reference_number.
        query = query.filter(Applicant.reference_number.isnot(None))

    if search:
        query = query.filter(
            (Applicant.full_name.ilike(f'%{search}%')) |
            (Applicant.contact_number.ilike(f'%{search}%'))
        )

    all_applicants = query.order_by(Applicant.registered_at.desc()).all()
    return render_template('admin/applicants.html', applicants=all_applicants, search=search, show_all=show_all)


@admin_bp.route('/applicants/<int:applicant_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_applicant(applicant_id):
    applicant = Applicant.query.get_or_404(applicant_id)

    if request.method == 'POST':
        applicant.full_name = request.form.get('full_name')
        applicant.age = int(request.form.get('age'))
        applicant.contact_number = request.form.get('contact_number')
        applicant.program_id = int(request.form.get('program_id'))

        db.session.commit()

        audit_service.log_action(current_user.username, 'Edited applicant', applicant.full_name)

        return redirect(url_for('admin.applicants'))

    programs = Program.query.all()
    return render_template('admin/edit_applicant.html', applicant=applicant, programs=programs)


@admin_bp.route('/applicants/<int:applicant_id>/delete', methods=['POST'])
@login_required
def delete_applicant(applicant_id):
    applicant = Applicant.query.get_or_404(applicant_id)
    full_name = applicant.full_name

    # Delete their attendance record(s) first - otherwise the database
    # would refuse to delete the applicant since Attendance rows
    # still point to them.
    Attendance.query.filter_by(applicant_id=applicant.id).delete()

    db.session.delete(applicant)
    db.session.commit()

    audit_service.log_action(current_user.username, 'Deleted applicant', full_name)

    return redirect(url_for('admin.applicants'))


# ---------- ATTENDANCE ----------

@admin_bp.route('/attendance')
@login_required
def attendance():
    batch_filter = request.args.get('batch_id', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = Attendance.query

    if batch_filter:
        query = query.filter(Attendance.exam_batch_id == int(batch_filter))
    if status_filter:
        query = query.filter(Attendance.status == status_filter)

    all_attendance = query.order_by(Attendance.verified_at.desc()).all()
    all_batches = ExamBatch.query.order_by(ExamBatch.exam_date).all()

    return render_template(
        'admin/attendance.html',
        records=all_attendance,
        batches=all_batches,
        batch_filter=batch_filter,
        status_filter=status_filter
    )


@admin_bp.route('/attendance/<int:attendance_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_attendance(attendance_id):
    record = Attendance.query.get_or_404(attendance_id)

    if request.method == 'POST':
        record.status = request.form.get('status')
        db.session.commit()

        audit_service.log_action(
            current_user.username,
            'Edited attendance record',
            f"{record.applicant.full_name} -> {record.status}"
        )

        return redirect(url_for('admin.attendance'))

    return render_template('admin/edit_attendance.html', record=record)


@admin_bp.route('/attendance/<int:attendance_id>/delete', methods=['POST'])
@login_required
def delete_attendance(attendance_id):
    record = Attendance.query.get_or_404(attendance_id)
    applicant_name = record.applicant.full_name

    db.session.delete(record)
    db.session.commit()

    audit_service.log_action(current_user.username, 'Deleted attendance record', applicant_name)

    return redirect(url_for('admin.attendance'))


# ---------- AUDIT LOGS (view/filter only - never editable or deletable) ----------

@admin_bp.route('/audit-logs')
@login_required
def audit_logs():
    actor_filter = request.args.get('actor', '').strip()
    search = request.args.get('search', '').strip()

    query = AuditLog.query

    if actor_filter:
        query = query.filter(AuditLog.actor == actor_filter)
    if search:
        query = query.filter(
            (AuditLog.action.ilike(f'%{search}%')) |
            (AuditLog.details.ilike(f'%{search}%'))
        )

    logs = query.order_by(AuditLog.timestamp.desc()).all()

    # Distinct list of actors seen so far, for the filter dropdown
    distinct_actors = [row[0] for row in db.session.query(AuditLog.actor).distinct().all()]

    return render_template(
        'admin/audit_logs.html',
        logs=logs,
        distinct_actors=distinct_actors,
        actor_filter=actor_filter,
        search=search
    )