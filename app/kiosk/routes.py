from flask import Blueprint, render_template, request, redirect, url_for
from app.extensions import db
from app.models import Applicant, Program

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

        # TODO: redirect to face capture / batch selection next
        return redirect(url_for('kiosk.select_batch'))

    # GET request - just show the form
    programs = Program.query.all()
    return render_template('kiosk/register.html', programs=programs)


@kiosk_bp.route('/select-batch')
def select_batch():
    return render_template('kiosk/select_batch.html')


@kiosk_bp.route('/verify')
def verify():
    return render_template('kiosk/verify.html')


@kiosk_bp.route('/confirmation')
def confirmation():
    return render_template('kiosk/confirmation.html')