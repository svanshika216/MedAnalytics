from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models import Department, Doctor, DoctorAvailability, Appointment, User
from app.routes.auth import role_required
from datetime import datetime 
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    from sqlalchemy import func, text
    from datetime import datetime
    from app.models import Patient, Doctor, Appointment, PharmacyInventory

    today = datetime.utcnow().date()

    total_patients = Patient.query.count()
    total_doctors = Doctor.query.count()
    todays_appointments = Appointment.query.filter(
        func.date(Appointment.scheduled_time) == today
    ).count()
    low_stock = db.session.execute(text("""
        SELECT COUNT(*) FROM pharmacy_inventory
        WHERE quantity <= reorder_threshold
    """)).scalar()

    return render_template('admin/dashboard.html',
                           total_patients=total_patients,
                           total_doctors=total_doctors,
                           todays_appointments=todays_appointments,
                           low_stock=low_stock)

@admin_bp.route('/departments')
@login_required
@role_required('admin')
def departments():
    all_departments = Department.query.order_by(Department.name).all()
    return render_template('admin/departments.html', departments=all_departments)

@admin_bp.route('/departments/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_department():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Department name cannot be empty','danger')
            return redirect(url_for('admin.add_department'))
        existing = Department.query.filter_by(name=name).first()
        if existing:
            flash('A department with that name already exists', 'danger')
            return redirect(url_for('admin.add_department'))
        dept = Department(name=name, is_default=False)
        db.session.add(dept)
        db.session.commit()
        flash(f'Department "{name}" added successfully.', 'success')
        return redirect(url_for('admin.departments'))
    return render_template('admin/add_department.html')

@admin_bp.route('/departments/edit/<int:dept_id>', methods=['GET','POST'])
@login_required
@role_required('admin')
def edit_department(dept_id):
    dept = Department.query.get_or_404(dept_id)
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        if not name:
            flash('Department name cannot be empty.','danger')
            return redirect(url_for('admin.edit_department', dept_id=dept_id))
        existing = Department.query.filter_by(name=name).first()
        if existing and existing.id != dept_id:
            flash('A department with that name already exists.', 'danger')
            return redirect(url_for('admin.edit_department', dept_id=dept_id))
        dept.name=name
        db.session.commit()
        flash(f'Department updated successfully', 'success')
        return redirect(url_for('admin.departments'))
    return render_template('admin/edit_department.html', dept=dept)


@admin_bp.route('/departments/delete/<int:dept_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_department(dept_id):
    dept = Department.query.get_or_404(dept_id)
    if dept.doctors:
        flash('Cannot delete departments - doctors are assigned to it', 'danger')
        return redirect(url_for('admin.departments'))
    db.session.delete(dept)
    db.session.commit()
    flash(f'Department "{dept.name}" deleted', 'success')
    return redirect(url_for('admin.departments'))

@admin_bp.route('/doctors')
@login_required
@role_required('admin')
def doctors():
    all_doctors = Doctor.query.join(Department).order_by(Doctor.name).all()
    return render_template('admin/doctors.html', doctors=all_doctors)

@admin_bp.route('/doctors/add', methods=['GET','POST'])
@login_required
@role_required('admin')  
def add_doctor():
    departments = Department.query.order_by(Department.name).all()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        specialization = request.form.get('specialization','').strip()
        contact = request.form.get('contact', '').strip()
        consultation_fee = request.form.get('consultation_fee', 500.00)
        department_id = request.form.get('department_id')

        if not all([name, specialization, contact, department_id]):
            flash('All fields are required', 'danger')
            return render_template('admin/add_doctor.html', departments=departments)
        
        doctor = Doctor(
            name=name,
            specialization=specialization,
            contact=contact,
            consultation_fee=float(consultation_fee),
            department_id=int(department_id)
        )
        db.session.add(doctor)
        db.session.flush()

        days = request.form.getlist('day_of_week') or []
        start_times = request.form.getlist('start_time') or []
        end_times = request.form.getlist('end_time') or []

        for day, start, end in zip(days, start_times, end_times):
            if day and start and end:
                avail = DoctorAvailability(
                    doctor_id=doctor.id,
                    day_of_week=day,
                    start_time=datetime.strptime(start,'%H:%M').time(),
                    end_time=datetime.strptime(end, '%H:%M').time()
                )
                db.session.add(avail)

        db.session.commit()
        flash(f'Dr. {name} added successfully.', 'success')
        return redirect(url_for('admin.doctors'))
        
    return render_template('admin/add_doctor.html', departments=departments)

@admin_bp.route('doctors/edit/<int:doctor_id>', methods=['GET','POST'])
@login_required
@role_required('admin')
def edit_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    departments = Department.query.order_by(Department.name).all()

    if request.method == 'POST':
        doctor.name = request.form.get('name','').strip()
        doctor.specialization = request.form.get('specialization','').strip()
        doctor.contact = request.form.get('contact','').strip()
        doctor.consultation_fee = float(request.form.get('consultation_fee', 500.00))
        doctor.department_id = request.form.get('department_id')

        DoctorAvailability.query.filter_by(doctor_id=doctor.id).delete()

        days = request.form.getlist('day_of_week') or []
        start_times = request.form.getlist('start_time') or []
        end_times = request.form.getlist('end_time') or []

        for day, start, end in zip(days, start_times, end_times):
            if day and start and end and ':' in start and ':' in end:
                try:
                    avail = DoctorAvailability(
                        doctor_id=doctor.id,
                        day_of_week=day,
                        start_time=datetime.strptime(start, '%H:%M').time(),
                        end_time=datetime.strptime(end, '%H:%M').time()
                    )
                    db.session.add(avail)
                except ValueError:
                    continue
            

        db.session.commit()
        flash(f'Dr. {doctor.name} updated.successfully','success')
        return redirect(url_for('admin.doctors'))
    
    return render_template('admin/edit_doctor.html', doctor=doctor, departments=departments)

@admin_bp.route('/doctors/delete/<int:doctor_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    if doctor.appointments:
        flash('Cannot delete doctor - appointments exist for this doctor.', 'danger')
        return redirect(url_for('admin.doctors'))
    
    db.session.delete(doctor)
    db.session.commit()
    flash(f'Dr. {doctor.name} deleted.', 'success')
    return redirect(url_for('admin.doctors'))

@admin_bp.route('/doctors/view/<int:doctor_id>')
@login_required
@role_required('admin')
def view_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    return render_template('admin/view_doctor.html', doctor=doctor)


@admin_bp.route('/users')
@login_required
@role_required('admin')
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_user():
    doctors = Doctor.query.order_by(Doctor.name).all()
    # only doctors without an account yet
    doctors_without_account = [d for d in doctors if d.user is None]

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role')
        doctor_id = request.form.get('doctor_id') or None

        if not all([username, password, role]):
            flash('Username, password and role are required.', 'danger')
            return render_template('admin/add_user.html',
                                   doctors=doctors_without_account)

        existing = User.query.filter_by(username=username).first()
        if existing:
            flash('Username already taken.', 'danger')
            return render_template('admin/add_user.html',
                                   doctors=doctors_without_account)

        if role == 'doctor' and not doctor_id:
            flash('Please select a doctor profile for doctor accounts.', 'danger')
            return render_template('admin/add_user.html',
                                   doctors=doctors_without_account)

        user = User(
            username=username,
            role=role,
            doctor_id=int(doctor_id) if doctor_id else None
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash(f'User "{username}" created successfully.', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/add_user.html', doctors=doctors_without_account)


@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.username == 'admin':
        flash('Cannot delete the main admin account.', 'danger')
        return redirect(url_for('admin.users'))
    db.session.delete(user)
    db.session.commit()
    flash(f'User "{user.username}" deleted.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/reset-password/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password', '').strip()
    if not new_password:
        flash('Password cannot be empty.', 'danger')
        return redirect(url_for('admin.users'))
    user.set_password(new_password)
    db.session.commit()
    flash(f'Password reset for "{user.username}".', 'success')
    return redirect(url_for('admin.users'))



    