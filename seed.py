from app import create_app, db
from app.models import (Department, Doctor, DoctorAvailability, Patient,
                        Appointment, Prescription, PharmacyInventory, Billing, User)
from datetime import datetime, timedelta, time
import random

app = create_app()

with app.app_context():

    # ── Departments ──────────────────────────────────────────────
    dept_names = [
        'General Medicine', 'Cardiology', 'Neurology', 'Orthopedics',
        'Pediatrics', 'Gynecology', 'Dermatology', 'Pharmacy'
    ]
    depts = {}
    for name in dept_names:
        d = Department.query.filter_by(name=name).first()
        if not d:
            d = Department(name=name, is_default=True)
            db.session.add(d)
            db.session.flush()
        depts[name] = d
    db.session.commit()
    print("Departments done.")

    # ── Doctors ───────────────────────────────────────────────────
    doctors_data = [
        ('Arjun Mehta',     'Cardiologist',      '9810001001', 'Cardiology',       800.00),
        ('Priya Sharma',    'Neurologist',        '9810001002', 'Neurology',        900.00),
        ('Ravi Kumar',      'Orthopedic Surgeon', '9810001003', 'Orthopedics',      750.00),
        ('Sneha Reddy',     'Pediatrician',       '9810001004', 'Pediatrics',       600.00),
        ('Amit Gupta',      'General Physician',  '9810001005', 'General Medicine', 500.00),
        ('Kavita Joshi',    'Gynecologist',       '9810001006', 'Gynecology',       700.00),
        ('Rohit Verma',     'Dermatologist',      '9810001007', 'Dermatology',      650.00),
        ('Deepa Nair',      'General Physician',  '9810001008', 'General Medicine', 500.00),
    ]

    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    doctor_objs = []

    for name, spec, contact, dept_name, fee in doctors_data:
        doc = Doctor.query.filter_by(contact=contact).first()
        if not doc:
            doc = Doctor(
                name=name, specialization=spec, contact=contact,
                department_id=depts[dept_name].id, consultation_fee=fee
            )
            db.session.add(doc)
            db.session.flush()

            for day in days:
                avail = DoctorAvailability(
                    doctor_id=doc.id, day_of_week=day,
                    start_time=time(9, 0), end_time=time(17, 0)
                )
                db.session.add(avail)
        doctor_objs.append(doc)

    db.session.commit()
    print("Doctors done.")

    # ── Patients ──────────────────────────────────────────────────
    patients_data = [
        ('Rahul Verma',     '1990-03-15', 'Male',   'B+',  '9900001001'),
        ('Anjali Singh',    '1985-07-22', 'Female', 'A+',  '9900001002'),
        ('Suresh Patel',    '1978-11-30', 'Male',   'O+',  '9900001003'),
        ('Meena Sharma',    '1995-01-10', 'Female', 'AB+', '9900001004'),
        ('Vikram Rao',      '1982-05-18', 'Male',   'B-',  '9900001005'),
        ('Pooja Mehta',     '1993-08-25', 'Female', 'A-',  '9900001006'),
        ('Anil Kumar',      '1970-12-05', 'Male',   'O-',  '9900001007'),
        ('Sunita Gupta',    '1988-04-14', 'Female', 'B+',  '9900001008'),
        ('Manoj Tiwari',    '1975-09-20', 'Male',   'A+',  '9900001009'),
        ('Rekha Joshi',     '1991-06-08', 'Female', 'O+',  '9900001010'),
        ('Deepak Nair',     '1983-02-28', 'Male',   'AB-', '9900001011'),
        ('Kavya Reddy',     '1997-10-17', 'Female', 'B+',  '9900001012'),
        ('Sanjay Mishra',   '1969-07-03', 'Male',   'A+',  '9900001013'),
        ('Lata Pandey',     '1986-03-22', 'Female', 'O+',  '9900001014'),
        ('Rajan Kapoor',    '1980-11-11', 'Male',   'B-',  '9900001015'),
    ]

    patient_objs = []
    for name, dob, gender, bg, contact in patients_data:
        p = Patient.query.filter_by(contact=contact).first()
        if not p:
            p = Patient(
                name=name,
                dob=datetime.strptime(dob, '%Y-%m-%d').date(),
                gender=gender, blood_group=bg, contact=contact
            )
            db.session.add(p)
            db.session.flush()
        patient_objs.append(p)

    db.session.commit()
    print("Patients done.")

    # ── Medicines ─────────────────────────────────────────────────
    medicines_data = [
        ('Paracetamol 500mg',   200, 20, 5.00),
        ('Amoxicillin 250mg',   150, 15, 12.00),
        ('Ibuprofen 400mg',     180, 20, 8.00),
        ('Omeprazole 20mg',     120, 15, 15.00),
        ('Metformin 500mg',     100, 10, 6.00),
        ('Atorvastatin 10mg',    80, 10, 25.00),
        ('Amlodipine 5mg',       90, 10, 18.00),
        ('Cetirizine 10mg',     160, 20, 4.00),
        ('Azithromycin 500mg',   60,  8, 35.00),
        ('Pantoprazole 40mg',   110, 15, 20.00),
    ]

    for name, qty, threshold, price in medicines_data:
        m = PharmacyInventory.query.filter_by(medicine_name=name).first()
        if not m:
            m = PharmacyInventory(
                medicine_name=name, quantity=qty,
                reorder_threshold=threshold, unit_price=price
            )
            db.session.add(m)

    db.session.commit()
    print("Medicines done.")

    # ── Appointments + Prescriptions + Billing ────────────────────
    priorities = ['normal', 'normal', 'normal', 'urgent', 'emergency']
    statuses   = ['completed', 'completed', 'completed', 'scheduled', 'cancelled']
    medicine_names = [m[0] for m in medicines_data]

    base_date = datetime.utcnow() - timedelta(days=90)
    appointment_count = 0

    for i in range(120):
        patient = random.choice(patient_objs)
        doctor  = random.choice(doctor_objs)
        priority = random.choice(priorities)
        status   = random.choice(statuses)

        # random weekday within last 90 days
        days_offset = random.randint(0, 89)
        appt_date = base_date + timedelta(days=days_offset)
        # make sure it lands on a weekday
        while appt_date.weekday() > 4:
            appt_date += timedelta(days=1)

        hour = random.choice([9, 10, 11, 12, 14, 15, 16])
        scheduled_time = appt_date.replace(
            hour=hour, minute=0, second=0, microsecond=0
        )

        appt = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            department_id=doctor.department_id,
            scheduled_time=scheduled_time,
            priority=priority,
            status=status
        )
        db.session.add(appt)
        db.session.flush()

        # billing
        extra = random.uniform(0, 300)
        bill = Billing(
            appointment_id=appt.id,
            total_amount=round(float(doctor.consultation_fee) + extra, 2),
            payment_status='paid' if status == 'completed' else 'pending',
            generated_at=scheduled_time
        )
        db.session.add(bill)

        # prescriptions for completed appointments
        if status == 'completed':
            num_rx = random.randint(1, 3)
            for _ in range(num_rx):
                med = random.choice(medicine_names)
                rx = Prescription(
                    appointment_id=appt.id,
                    medicine_name=med,
                    dosage=random.choice(['1 tablet twice daily',
                                          '1 tablet three times daily',
                                          '2 tablets once daily']),
                    duration=random.choice(['3 days', '5 days', '7 days', '10 days']),
                )
                db.session.add(rx)

                inv = PharmacyInventory.query.filter_by(medicine_name=med).first()
                if inv and inv.quantity > 0:
                    inv.quantity -= 1

        appointment_count += 1

    db.session.commit()
    print(f"Appointments done — {appointment_count} created.")

    # ── Admin user ────────────────────────────────────────────────
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

    print("Seed complete.")