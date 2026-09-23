from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Program, ExamBatch
from app.services.batch_service import refresh_batch_status, is_batch_editable

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

        return redirect(url_for('admin.programs'))

    all_programs = Program.query.all()
    return render_template('admin/programs.html', programs=all_programs)


@admin_bp.route('/programs/<int:program_id>/delete', methods=['POST'])
@login_required
def delete_program(program_id):
    program = Program.query.get_or_404(program_id)
    db.session.delete(program)
    db.session.commit()
    return redirect(url_for('admin.programs'))


# ---------- EXAM BATCHES ----------

@admin_bp.route('/batches', methods=['GET', 'POST'])
@login_required
def batches():
    if request.method == 'POST':
        batch_name = request.form.get('batch_name')
        exam_date = datetime.strptime(request.form.get('exam_date'), '%Y-%m-%d').date()
        start_time = datetime.strptime(request.form.get('start_time'), '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(request.form.get('end_time'), '%Y-%m-%dT%H:%M')
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

        return redirect(url_for('admin.batches'))

    # GET request - refresh every batch's status before showing the list
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
        batch.start_time = datetime.strptime(request.form.get('start_time'), '%Y-%m-%dT%H:%M')
        batch.end_time = datetime.strptime(request.form.get('end_time'), '%Y-%m-%dT%H:%M')
        batch.capacity = int(request.form.get('capacity'))
        batch.venue = request.form.get('venue')

        db.session.commit()
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

    db.session.delete(batch)
    db.session.commit()
    return redirect(url_for('admin.batches'))