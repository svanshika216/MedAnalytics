from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    doctors = db.relationship('Doctor', backref='department', lazy=True)

    def __repr__(self):
        return f'<Department {self.name}>'
    
class Doctor(db.Model):
    __tablename__ = 'doctors'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(15), nullable=False)
    consultation_fee = db.Column(db.Numeric(10, 2), nullable=False, default=500.00)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    availability = db.relationship('DoctorAvailability', backref='doctor', lazy=True, cascade='all, delete-orphan')
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)
    user = db.relationship('User', backref='doctor', lazy=True, uselist=False)

    def __repr__(self):
        return f'<Doctor {self.name}>'
    
class DoctorAvailability(db.Model):
    __tablename__ = 'doctor_availability'

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    day_of_week = db.Column(db.String(10), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    def __repr__(self):
        return f'<Availability {self.doctor_id} {self.day_of_week}>'
    
class Patient(db.Model):
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    blood_group = db.Column(db.String(5))
    contact = db.Column(db.String(15), nullable=False)
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    appointments = db.relationship('Appointment', backref='patient', lazy=True)

    def __repr__(self):
        return f'<Patient {self.name}>'
    
class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    scheduled_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='scheduled')
    priority = db.Column(db.String(20), default='normal')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    prescriptions = db.relationship('Prescription', backref='appointment', lazy=True, cascade='all, delete-orphan')
    billing = db.relationship('Billing', backref='appointment',lazy=True, uselist=False, cascade='all, delete-orphan')
    department = db.relationship('Department', backref='appointment', lazy=True)


    def __repr__(self):
        return f'<Appointment {self.id} - {self.status}>'
    
class Prescription(db.Model):
    __tablename__ = 'prescriptions'

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    medicine_name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50), nullable=False)
    duration = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Prescription {self.medicine_name}>'
    
class PharmacyInventory(db.Model):
    __tablename__ = 'pharmacy_inventory'

    id = db.Column(db.Integer, primary_key=True)
    medicine_name = db.Column(db.String(100), nullable=False, unique=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    reorder_threshold = db.Column(db.Integer, nullable=False, default=10)
    unit_price = db.Column(db.Numeric(10,2), nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Medicine {self.medicine_name}>'
    
class Billing(db.Model):
    __tablename__ = 'billing'

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False, unique=True)
    total_amount = db.Column(db.Numeric(10,2), nullable=False, default=0.00)
    payment_status = db.Column(db.String(20), default='pending')
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Billinf {self.id} - {self.payment_status}>'
    
class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=True, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self,password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} - {self.role}>'

