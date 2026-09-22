from flask import Blueprint, render_template
from flask_login import login_required

# This blueprint holds the actual admin pages (dashboard, batches, etc).
admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('admin/dashboard.html')