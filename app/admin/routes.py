"""
Admin routes - narratives Version 1.1:
  2.2 Manage Exam Schedule  (create / view / update / delete batches)
  2.3 View Attendance       (read-only list, batch filter, CSV export)
Login (2.1) lives in auth.py.
"""
import csv
import io
from datetime import date, datetime

from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, Response)
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import ExamBatch, Applicant, Attendance

admin_bp = Blueprint('admin', __name__)


# ==========================================================================
# DASHBOARD
# ==========================================================================

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    # Overall numbers, not just today's: the kiosk is used across many batches.
    registrations_total = Applicant.query.count()
    time_ins_total = Attendance.query.count()
    batches_total = ExamBatch.query.count()

    all_batches = (ExamBatch.query
                   .order_by(ExamBatch.exam_date, ExamBatch.start_time).all())
    upcoming_batches = [b for b in all_batches if not b.has_ended][:5]

    recent_attendance = (Attendance.query
                         .order_by(Attendance.timed_in_at.desc())
                         .limit(6).all())

    return render_template(
        'admin/dashboard.html',
        registrations_total=registrations_total,
        time_ins_total=time_ins_total,
        batches_total=batches_total,
        upcoming_batches=upcoming_batches,
        recent_attendance=recent_attendance,
    )


# ==========================================================================
# 2.2 MANAGE EXAM SCHEDULE
# ==========================================================================

def _read_batch_form(allow_past=False):
    """
    Read and validate the batch form (Step 4).
    Returns (values_dict, error_message). error_message is None when valid.

    A new batch must be scheduled for today or later; an existing batch may
    keep a past date when it is only being corrected.
    """
    try:
        exam_date = datetime.strptime(request.form.get('exam_date', ''), '%Y-%m-%d').date()
        start_time = datetime.strptime(request.form.get('start_time', ''), '%H:%M').time()
        end_time = datetime.strptime(request.form.get('end_time', ''), '%H:%M').time()
        capacity = int(request.form.get('capacity', ''))
    except ValueError:
        return None, "Please fill in the date, start and end time, and capacity correctly."

    building = request.form.get('building', '').strip()
    room = request.form.get('room', '').strip()

    if not building or not room:
        return None, "Building and room are required."
    if end_time <= start_time:
        return None, "End time must be after the start time."
    if capacity < 1:
        return None, "Capacity must be at least 1."

    if not allow_past:
        if exam_date < date.today():
            return None, "The exam date can't be in the past."
        # A window that already ended earlier today can't be created either.
        if exam_date == date.today() and end_time <= datetime.now().time():
            return None, "That window has already ended today. Choose a later end time."

    return {
        'exam_date': exam_date,
        'start_time': start_time,
        'end_time': end_time,
        'building': building,
        'room': room,
        'capacity': capacity,
    }, None


def _blocked_reason(batch, for_delete=False):
    """Why a batch can't be updated/deleted, or None if it can (2.2).

    Edit requires a future batch with no applicants. Delete is a little more
    forgiving: an ended batch that nobody attended can still be cleaned up.
    """
    if batch.is_ongoing:
        return "This batch is ongoing, so it can't be changed."
    if batch.has_ended and not for_delete:
        return "This batch has already ended, so it can't be changed."
    if batch.reserved_seats > 0:
        return ("This batch already has applicants assigned or reserved, "
                "so it can't be changed.")
    return None


@admin_bp.route('/batches', methods=['GET', 'POST'])
@login_required
def batches():
    if request.method == 'POST':
        values, error = _read_batch_form()
        if error:
            flash(error, 'error')
            return redirect(url_for('admin.batches'))

        # The batch ID is assigned automatically by the database.
        db.session.add(ExamBatch(created_by=current_user.id, **values))
        db.session.commit()
        flash("Batch created.", 'success')
        return redirect(url_for('admin.batches'))

    all_batches = (ExamBatch.query
                   .order_by(ExamBatch.exam_date, ExamBatch.start_time).all())

    # ?edit=<id> opens that batch in the edit dialog (same pattern as Create).
    editing = None
    edit_id = request.args.get('edit', type=int)
    if edit_id:
        candidate = db.session.get(ExamBatch, edit_id)
        if candidate is None:
            flash("That batch no longer exists.", 'error')
        else:
            reason = _blocked_reason(candidate)
            if reason:
                flash(reason, 'error')
            else:
                editing = candidate

    return render_template('admin/batches.html', batches=all_batches, editing=editing)


@admin_bp.route('/batches/<int:batch_id>/edit', methods=['POST'])
@login_required
def edit_batch(batch_id):
    batch = ExamBatch.query.get_or_404(batch_id)

    reason = _blocked_reason(batch)
    if reason:
        flash(reason, 'error')
        return redirect(url_for('admin.batches'))

    values, error = _read_batch_form(allow_past=True)
    if error:
        flash(error, 'error')
        return redirect(url_for('admin.batches', edit=batch.id))

    for field, value in values.items():
        setattr(batch, field, value)
    db.session.commit()
    flash("Batch updated.", 'success')
    return redirect(url_for('admin.batches'))


@admin_bp.route('/batches/<int:batch_id>/delete', methods=['POST'])
@login_required
def delete_batch(batch_id):
    batch = ExamBatch.query.get_or_404(batch_id)

    reason = _blocked_reason(batch, for_delete=True)
    if reason:
        flash(reason, 'error')
        return redirect(url_for('admin.batches'))

    db.session.delete(batch)
    db.session.commit()
    flash("Batch deleted.", 'success')
    return redirect(url_for('admin.batches'))


# ==========================================================================
# 2.3 VIEW ATTENDANCE  (read-only)
# ==========================================================================

def _attendance_rows(batch_id):
    """Every registered applicant, with their time-in if they have one.

    A LEFT JOIN keeps students who have not timed in yet in the list: they
    show "Not yet timed in" until the batch closes, then "Absent".
    """
    query = (db.session.query(Applicant, Attendance)
             .options(joinedload(Applicant.exam_batch))
             .outerjoin(Attendance, Attendance.applicant_id == Applicant.id))
    if batch_id:
        query = query.filter(Applicant.exam_batch_id == batch_id)
    return query.order_by(
        Attendance.timed_in_at.desc().nullslast(),
        Applicant.last_name, Applicant.first_name,
    ).all()


@admin_bp.route('/attendance')
@login_required
def attendance():
    batch_filter = request.args.get('batch_id', type=int)
    rows = _attendance_rows(batch_filter)
    all_batches = (ExamBatch.query
                   .order_by(ExamBatch.exam_date, ExamBatch.start_time).all())

    # The template shows a "No records" message when `rows` is empty.
    return render_template(
        'admin/attendance.html',
        rows=rows,
        batches=all_batches,
        batch_filter=batch_filter,
    )


def _csv_safe(value):
    """Stop spreadsheet formula injection (a name like '=1+1' opening as a formula)."""
    text = '' if value is None else str(value)
    return "'" + text if text[:1] in ('=', '+', '-', '@') else text


@admin_bp.route('/attendance/export')
@login_required
def export_attendance():
    batch_filter = request.args.get('batch_id', type=int)
    rows = _attendance_rows(batch_filter)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['Full Name', 'Registration Number', 'Batch ID',
                     'Time-In Timestamp', 'Reference Number', 'Status'])
    for applicant, record in rows:
        if record:
            status = 'Present'
        elif applicant.exam_batch.has_ended:
            status = 'Absent'
        else:
            status = 'Not yet timed in'

        writer.writerow([
            _csv_safe(applicant.full_name),
            applicant.registration_number,
            applicant.exam_batch_id,
            record.timed_in_at.strftime('%Y-%m-%d %H:%M:%S') if record else '',
            record.reference_number if record else '',
            status,
        ])

    filename = f"attendance_batch_{batch_filter}.csv" if batch_filter else "attendance_all.csv"
    return Response(
        '\ufeff' + buffer.getvalue(),   # BOM so Excel reads UTF-8 names correctly
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'},
    )