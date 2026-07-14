from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Appointment, Patient, Doctor, Department, Billing
from app.routes.auth import role_required
from app.scheduler.engine import AppointmentScheduler
from datetime import datetime
from flask import jsonify

appointments_bp = Blueprint('appointments', __name__, url_prefix='/appointments')


@appointments_bp.route('/')
@login_required
@role_required('admin', 'receptionist', 'doctor')
def list_appointments():
    if current_user.role == 'doctor':
        appointments = Appointment.query.filter_by(
            doctor_id=current_user.doctor_id
        ).order_by(Appointment.scheduled_time.desc()).all()
    else:
        appointments = Appointment.query.order_by(
            Appointment.scheduled_time.desc()
        ).all()
    return render_template('appointments/list.html', appointments=appointments)


@appointments_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'receptionist')
def add_appointment():
    patients = Patient.query.order_by(Patient.name).all()
    doctors = Doctor.query.order_by(Doctor.name).all()
    departments = Department.query.order_by(Department.name).all()

    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        doctor_id = request.form.get('doctor_id')
        department_id = request.form.get('department_id')
        scheduled_time_str = request.form.get('scheduled_time')
        priority = request.form.get('priority', 'normal')
        notes = request.form.get('notes', '').strip()

        if not all([patient_id, doctor_id, department_id, scheduled_time_str]):
            flash('All fields are required.', 'danger')
            return render_template('appointments/add.html',
                                   patients=patients, doctors=doctors,
                                   departments=departments)

        scheduled_time = datetime.strptime(scheduled_time_str, '%Y-%m-%dT%H:%M')
        doctor = Doctor.query.get(int(doctor_id))

        # Step 1 — check doctor availability
        if not AppointmentScheduler.check_doctor_available(doctor, scheduled_time):
            suggested = AppointmentScheduler.suggest_next_slot(doctor, scheduled_time)
            if suggested:
                flash(f'Dr. {doctor.name} is not available at that time. '
                      f'Next available slot: {suggested.strftime("%d %b %Y %I:%M %p")}',
                      'warning')
            else:
                flash(f'Dr. {doctor.name} has no availability on that day.', 'danger')
            return render_template('appointments/add.html',
                                   patients=patients, doctors=doctors,
                                   departments=departments)

        # Step 2 — check slot conflict
        if AppointmentScheduler.check_slot_conflict(int(doctor_id), scheduled_time):
            suggested = AppointmentScheduler.suggest_next_slot(doctor, scheduled_time)
            if suggested:
                flash(f'That slot is already booked. '
                      f'Next available slot: {suggested.strftime("%d %b %Y %I:%M %p")}',
                      'warning')
            else:
                flash('No available slots found for that day.', 'danger')
            return render_template('appointments/add.html',
                                   patients=patients, doctors=doctors,
                                   departments=departments)

        # Step 3 — create appointment
        appointment = Appointment(
            patient_id=int(patient_id),
            doctor_id=int(doctor_id),
            department_id=int(department_id),
            scheduled_time=scheduled_time,
            priority=priority,
            notes=notes or None
        )
        db.session.add(appointment)
        db.session.flush()

        # Step 4 — push to scheduler heap
        scheduler = AppointmentScheduler()
        scheduler.push(appointment)

        # Step 5 — auto-generate billing record
        billing = Billing(
            appointment_id=appointment.id,
            total_amount=doctor.consultation_fee,
            payment_status='pending'
        )
        db.session.add(billing)
        db.session.commit()

        flash(f'Appointment booked successfully for '
              f'{appointment.patient.name} with Dr. {doctor.name}.', 'success')
        return redirect(url_for('appointments.list_appointments'))

    return render_template('appointments/add.html',
                           patients=patients, doctors=doctors,
                           departments=departments)

@appointments_bp.route('/doctors-by-department/<int:dept_id>')
@login_required
def doctors_by_department(dept_id):
    doctors = Doctor.query.filter_by(department_id=dept_id).order_by(Doctor.name).all()
    return jsonify([{
        'id': d.id,
        'name': d.name,
        'specialization': d.specialization,
        'consultation_fee': float(d.consultation_fee)
    } for d in doctors])


@appointments_bp.route('/view/<int:appointment_id>')
@login_required
@role_required('admin', 'receptionist', 'doctor')
def view_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    if current_user.role == 'doctor':
        if appointment.doctor_id != current_user.doctor_id:
            flash('You can only view your own appointments.', 'danger')
            return redirect(url_for('appointments.list_appointments'))
    return render_template('appointments/view.html', appointment=appointment)


@appointments_bp.route('/status/<int:appointment_id>', methods=['POST'])
@login_required
@role_required('admin', 'doctor')
def update_status(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    if current_user.role == 'doctor':
        if appointment.doctor_id != current_user.doctor_id:
            flash('You can only update your own appointments.', 'danger')
            return redirect(url_for('appointments.list_appointments'))
    new_status = request.form.get('status')
    if new_status in ['scheduled', 'completed', 'cancelled']:
        appointment.status = new_status
        db.session.commit()
        flash(f'Appointment status updated to {new_status}.', 'success')
    return redirect(url_for('appointments.view_appointment',
                            appointment_id=appointment_id))


@appointments_bp.route('/prescribe/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
@role_required('doctor', 'admin')
def add_prescription(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    if current_user.role == 'doctor':
        if appointment.doctor_id != current_user.doctor_id:
            flash('You can only prescribe for your own appointments.', 'danger')
            return redirect(url_for('appointments.list_appointments'))

    if request.method == 'POST':
        from app.models import Prescription, PharmacyInventory
        medicines = request.form.getlist('medicine_name')
        dosages = request.form.getlist('dosage')
        durations = request.form.getlist('duration')
        notes_list = request.form.getlist('notes')

        for medicine, dosage, duration, notes in zip(
                medicines, dosages, durations, notes_list):
            if medicine and dosage and duration:
                from app.models import Prescription
                rx = Prescription(
                    appointment_id=appointment.id,
                    medicine_name=medicine,
                    dosage=dosage,
                    duration=duration,
                    notes=notes or None
                )
                db.session.add(rx)

                # deduct from inventory if medicine exists
                inventory_item = PharmacyInventory.query.filter_by(
                    medicine_name=medicine
                ).first()
                if inventory_item and inventory_item.quantity > 0:
                    inventory_item.quantity -= 1

        db.session.commit()
        flash('Prescriptions saved successfully.', 'success')
        return redirect(url_for('appointments.view_appointment',
                                appointment_id=appointment_id))

    return render_template('appointments/prescribe.html', appointment=appointment)