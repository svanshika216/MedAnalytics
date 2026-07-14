from flask import Blueprint, render_template
from flask_login import login_required
from app import db
from app.models import Patient, Doctor, Appointment, Billing, Prescription, PharmacyInventory
from app.routes.auth import role_required
from datetime import datetime, timedelta
from sqlalchemy import text, func

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')


def get_analytics_data():
    today = datetime.utcnow().date()
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    # --- basic counts ---
    total_patients = Patient.query.count()
    total_doctors = Doctor.query.count()
    total_appointments = Appointment.query.count()

    # today's appointments
    todays_appointments = Appointment.query.filter(
        func.date(Appointment.scheduled_time) == today
    ).count()

    # low stock count
    low_stock = db.session.execute(text("""
        SELECT COUNT(*) FROM pharmacy_inventory
        WHERE quantity <= reorder_threshold
    """)).scalar()

    # --- appointment status breakdown ---
    status_breakdown = db.session.execute(text("""
        SELECT status, COUNT(*) as count
        FROM appointments
        GROUP BY status
        ORDER BY count DESC
    """)).fetchall()

    # --- department wise appointment volume ---
    dept_volume = db.session.execute(text("""
        SELECT d.name as department, COUNT(a.id) as total
        FROM departments d
        LEFT JOIN appointments a ON a.department_id = d.id
        GROUP BY d.name
        ORDER BY total DESC
    """)).fetchall()

    # --- doctor utilization ---
    doctor_utilization = db.session.execute(text("""
        SELECT
            doc.name as doctor_name,
            dept.name as department,
            COUNT(a.id) as total_appointments,
            SUM(CASE WHEN a.status = 'completed' THEN 1 ELSE 0 END) as completed
        FROM doctors doc
        JOIN departments dept ON dept.id = doc.department_id
        LEFT JOIN appointments a ON a.doctor_id = doc.id
        GROUP BY doc.id, doc.name, dept.name
        ORDER BY total_appointments DESC
    """)).fetchall()

    # --- monthly revenue trend (last 6 months) ---
    revenue_trend = db.session.execute(text("""
        SELECT
            TO_CHAR(generated_at, 'Mon YYYY') as month,
            DATE_TRUNC('month', generated_at) as month_date,
            SUM(total_amount) as revenue,
            COUNT(*) as bills
        FROM billing
        WHERE payment_status = 'paid'
        AND generated_at >= NOW() - INTERVAL '6 months'
        GROUP BY month, month_date
        ORDER BY month_date ASC
    """)).fetchall()

    # --- top 5 prescribed medicines ---
    top_medicines = db.session.execute(text("""
        SELECT medicine_name, COUNT(*) as prescription_count
        FROM prescriptions
        GROUP BY medicine_name
        ORDER BY prescription_count DESC
        LIMIT 5
    """)).fetchall()

    # --- readmission rate ---
    # patients who had more than one appointment within any 30-day window
    readmissions = db.session.execute(text("""
        SELECT COUNT(DISTINCT a1.patient_id) as readmitted_patients
        FROM appointments a1
        JOIN appointments a2
            ON a1.patient_id = a2.patient_id
            AND a1.id != a2.id
            AND a2.scheduled_time BETWEEN a1.scheduled_time
            AND a1.scheduled_time + INTERVAL '30 days'
    """)).scalar()

    readmission_rate = 0
    if total_patients > 0:
        readmission_rate = round((readmissions / total_patients) * 100, 1)

    # --- priority breakdown ---
    priority_breakdown = db.session.execute(text("""
        SELECT priority, COUNT(*) as count
        FROM appointments
        GROUP BY priority
        ORDER BY count DESC
    """)).fetchall()

    return {
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'total_appointments': total_appointments,
        'todays_appointments': todays_appointments,
        'low_stock': low_stock,
        'status_breakdown': status_breakdown,
        'dept_volume': dept_volume,
        'doctor_utilization': doctor_utilization,
        'revenue_trend': revenue_trend,
        'top_medicines': top_medicines,
        'readmission_rate': readmission_rate,
        'readmitted_patients': readmissions,
        'priority_breakdown': priority_breakdown
    }


@analytics_bp.route('/')
@login_required
@role_required('admin')
def dashboard():
    data = get_analytics_data()
    return render_template('analytics/dashboard.html', data=data)