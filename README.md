# MedAnalytics — Hospital & Pharmacy Operations System

A full-stack hospital operations management system built with Flask and PostgreSQL, featuring a DSA-based intelligent appointment scheduling engine and a Power BI analytics dashboard.

---

## Project Overview

MedAnalytics is a backend-heavy internal system designed to manage hospital operations across three user roles — Admin, Doctor, and Receptionist. The project demonstrates relational database design, algorithmic problem-solving applied to a real business domain, and operational analytics using industry-standard BI tooling.

---

## Key Technical Highlights

**DSA Scheduling Engine** (`app/scheduler/engine.py`)
- Priority queue (min-heap) for appointment triage — emergency cases surface automatically over normal bookings
- Interval scheduling conflict detection — prevents double-booking within 30-minute windows
- Greedy slot-finder — suggests the next available slot when a requested time is unavailable
- Implemented using Python's `heapq` module with O(log n) push/pop operations

**PostgreSQL Schema Design**
- 8 normalized tables with proper foreign key constraints and cascade rules
- SQLAlchemy ORM for CRUD operations + raw SQL/SQLAlchemy Core for analytics queries
- Window functions, CTEs, and aggregations for operational analytics (doctor utilization, readmission rate, revenue trends)
- Schema versioning via Flask-Migrate (Alembic)

**Role-Based Access Control**
- Three roles: Admin, Doctor, Receptionist — each with enforced route-level permissions
- Custom `role_required` decorator applied at every protected route
- Doctor-scoped data access — doctors see only their own appointments and patients

**Power BI Dashboard** (5 pages)
- Connected directly to PostgreSQL via native connector
- Operations Overview, Patient & Appointment Trends, Doctor Performance, Pharmacy & Inventory, Revenue & Billing

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, Flask, SQLAlchemy |
| Database | PostgreSQL 18, Flask-Migrate |
| Frontend | Jinja2, Bootstrap 5 |
| Auth | Flask-Login, Flask-WTF (CSRF) |
| Analytics | Power BI Desktop |
| Dev Tools | Git, pgAdmin, VS Code |

---

## Modules

- **Patient Management** — registration, medical history, prescription records across visits
- **Doctor Management** — profiles, department assignment, weekly availability scheduling, consultation fees
- **Appointment Booking** — scheduler-validated booking with priority levels (normal/urgent/emergency)
- **Prescription System** — per-appointment prescriptions with automatic pharmacy inventory deduction
- **Pharmacy & Inventory** — stock management, reorder alerts, low stock highlighting
- **Billing** — auto-generated bills pre-filled with consultation fees, payment tracking
- **Analytics** — SQL-driven operational metrics: appointment trends, doctor utilization, readmission rate, revenue by department
- **User Management** — admin creates/manages accounts, links doctor profiles to login credentials

---

## Database Schema

    departments ──< doctors ──< appointments >── patients
                       │              │
                  availability    prescriptions
                                  billing
                  pharmacy_inventory (deducted on prescription)
                  users (linked to doctors for role-based login)


---

## Setup Instructions

**Prerequisites**
- Python 3.10+
- PostgreSQL 14+
- Git

**Installation**

```bash
git clone https://github.com/svanshika216/MedAnalytics.git
cd MedAnalytics
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

**Database Setup**

Create a PostgreSQL database and user, then create a `.env` file:

DB_USER=your_db_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=medanalytics
SECRET_KEY=your_secret_key


**Run Migrations & Seed Data**

```bash
flask --app run.py db upgrade
python seed.py
```

**Start the Application**

```bash
python run.py
```

Visit `http://127.0.0.1:5000` and log in with `admin` / `admin123`.

---

## Scheduling Engine — How It Works

When a receptionist books an appointment:

1. The scheduler checks the doctor's availability slots (day + time window) — interval check
2. It checks for existing appointments within a 30-minute window — conflict detection
3. If a conflict is found, a greedy algorithm walks forward in 30-minute increments to suggest the next free slot
4. The appointment is assigned a priority level and pushed onto a min-heap — emergency cases (priority 1) always surface before urgent (2) and normal (3)

This means the system never double-books, always respects doctor availability, and surfaces critical cases to the top of any queue — mirroring how a real hospital triage system works.

---

## Analytics Queries

Key SQL patterns used in `app/routes/analytics.py`:

- `GROUP BY` with `COUNT` and `SUM` for department volume and revenue aggregation
- `DATE_TRUNC` for monthly revenue trend grouping
- `SELF-JOIN` on appointments table for readmission rate calculation
- `CASE WHEN` inside aggregations for doctor completion rate
- `TO_CHAR` for human-readable month formatting


---

## Project Structure

    medanalytics/
    ├── app/
    │   ├── __init__.py          # App factory, extensions
    │   ├── models.py            # SQLAlchemy models (8 tables)
    │   ├── routes/
    │   │   ├── auth.py          # Login, logout, role_required decorator
    │   │   ├── admin.py         # Departments, doctors, users, dashboard
    │   │   ├── patients.py      # Patient CRUD
    │   │   ├── appointments.py  # Booking, prescriptions, status updates
    │   │   ├── pharmacy.py      # Inventory, billing
    │   │   └── analytics.py     # SQL analytics queries
    │   ├── scheduler/
    │   │   └── engine.py        # DSA scheduling engine
    │   ├── templates/           # Jinja2 templates
    │   └── static/css/          # Custom stylesheet
    ├── config.py                # Environment-based configuration
    ├── run.py                   # Application entry point
    ├── seed.py                  # Database seeding script
    └── requirements.txt

---

## Author

Vanshika Sharma — B.Tech Electronics & Computer Engineering

