from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Patient
from app.routes.auth import role_required

patients_bp = Blueprint('patients', __name__, url_prefix='/patients')


@patients_bp.route('/')
@login_required
@role_required('admin', 'receptionist', 'doctor')
def list_patients():
    search = request.args.get('search', '').strip()

    if current_user.role == 'doctor':
        # only show patients this doctor has seen
        doctor = current_user.doctor
        patient_ids = list(set([appt.patient_id for appt in doctor.appointments]))
        query = Patient.query.filter(Patient.id.in_(patient_ids))
    else:
        query = Patient.query

    if search:
        query = query.filter(
            Patient.name.ilike(f'%{search}%') |
            Patient.contact.ilike(f'%{search}%')
        )

    patients = query.order_by(Patient.name).all()
    return render_template('patients/list.html', patients=patients, search=search)


@patients_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'receptionist')
def add_patient():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        dob = request.form.get('dob')
        gender = request.form.get('gender')
        blood_group = request.form.get('blood_group', '').strip()
        contact = request.form.get('contact', '').strip()
        address = request.form.get('address', '').strip()

        if not all([name, dob, gender, contact]):
            flash('Name, date of birth, gender and contact are required.', 'danger')
            return redirect(url_for('patients.add_patient'))

        existing = Patient.query.filter_by(contact=contact).first()
        if existing:
            flash('A patient with this contact number already exists.', 'danger')
            return redirect(url_for('patients.add_patient'))

        from datetime import datetime
        patient = Patient(
            name=name,
            dob=datetime.strptime(dob, '%Y-%m-%d').date(),
            gender=gender,
            blood_group=blood_group or None,
            contact=contact,
            address=address or None
        )
        db.session.add(patient)
        db.session.commit()
        flash(f'Patient {name} registered successfully.', 'success')
        return redirect(url_for('patients.list_patients'))

    return render_template('patients/add.html')


@patients_bp.route('/edit/<int:patient_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'receptionist')
def edit_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)

    if request.method == 'POST':
        patient.name = request.form.get('name', '').strip()
        patient.gender = request.form.get('gender')
        patient.blood_group = request.form.get('blood_group', '').strip() or None
        patient.contact = request.form.get('contact', '').strip()
        patient.address = request.form.get('address', '').strip() or None

        from datetime import datetime
        dob = request.form.get('dob')
        if dob:
            patient.dob = datetime.strptime(dob, '%Y-%m-%d').date()

        db.session.commit()
        flash(f'Patient {patient.name} updated successfully.', 'success')
        return redirect(url_for('patients.list_patients'))

    return render_template('patients/edit.html', patient=patient)


@patients_bp.route('/view/<int:patient_id>')
@login_required
@role_required('admin', 'receptionist', 'doctor')
def view_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)

    if current_user.role == 'doctor':
        doctor = current_user.doctor
        patient_ids = [appt.patient_id for appt in doctor.appointments]
        if patient.id not in patient_ids:
            flash('You can only view records of your own patients.', 'danger')
            return redirect(url_for('patients.list_patients'))
        
    return render_template('patients/view.html', patient=patient)


@patients_bp.route('/delete/<int:patient_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if patient.appointments:
        flash('Cannot delete patient — appointment history exists.', 'danger')
        return redirect(url_for('patients.list_patients'))
    db.session.delete(patient)
    db.session.commit()
    flash(f'Patient {patient.name} deleted.', 'success')
    return redirect(url_for('patients.list_patients'))