from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models import PharmacyInventory, Billing, Appointment
from app.routes.auth import role_required

pharmacy_bp = Blueprint('pharmacy', __name__, url_prefix='/pharmacy')


@pharmacy_bp.route('/')
@login_required
@role_required('admin', 'receptionist')
def inventory():
    medicines = PharmacyInventory.query.order_by(PharmacyInventory.medicine_name).all()
    low_stock = [m for m in medicines if m.quantity <= m.reorder_threshold]
    return render_template('pharmacy/inventory.html',
                           medicines=medicines, low_stock_count=len(low_stock))


@pharmacy_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_medicine():
    if request.method == 'POST':
        name = request.form.get('medicine_name', '').strip()
        quantity = request.form.get('quantity', 0)
        reorder_threshold = request.form.get('reorder_threshold', 10)
        unit_price = request.form.get('unit_price', 0)

        if not all([name, quantity, unit_price]):
            flash('Medicine name, quantity and unit price are required.', 'danger')
            return redirect(url_for('pharmacy.add_medicine'))

        existing = PharmacyInventory.query.filter_by(medicine_name=name).first()
        if existing:
            flash('Medicine already exists in inventory.', 'danger')
            return redirect(url_for('pharmacy.add_medicine'))

        medicine = PharmacyInventory(
            medicine_name=name,
            quantity=int(quantity),
            reorder_threshold=int(reorder_threshold),
            unit_price=float(unit_price)
        )
        db.session.add(medicine)
        db.session.commit()
        flash(f'{name} added to inventory.', 'success')
        return redirect(url_for('pharmacy.inventory'))

    return render_template('pharmacy/add_medicine.html')


@pharmacy_bp.route('/edit/<int:medicine_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_medicine(medicine_id):
    medicine = PharmacyInventory.query.get_or_404(medicine_id)

    if request.method == 'POST':
        medicine.medicine_name = request.form.get('medicine_name', '').strip()
        medicine.quantity = int(request.form.get('quantity', 0))
        medicine.reorder_threshold = int(request.form.get('reorder_threshold', 10))
        medicine.unit_price = float(request.form.get('unit_price', 0))
        db.session.commit()
        flash(f'{medicine.medicine_name} updated.', 'success')
        return redirect(url_for('pharmacy.inventory'))

    return render_template('pharmacy/edit_medicine.html', medicine=medicine)


@pharmacy_bp.route('/delete/<int:medicine_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_medicine(medicine_id):
    medicine = PharmacyInventory.query.get_or_404(medicine_id)
    db.session.delete(medicine)
    db.session.commit()
    flash(f'{medicine.medicine_name} removed from inventory.', 'success')
    return redirect(url_for('pharmacy.inventory'))


@pharmacy_bp.route('/billing')
@login_required
@role_required('admin', 'receptionist')
def billing_list():
    billings = Billing.query.order_by(Billing.generated_at.desc()).all()
    return render_template('pharmacy/billing.html', billings=billings)


@pharmacy_bp.route('/billing/pay/<int:billing_id>', methods=['POST'])
@login_required
@role_required('admin', 'receptionist')
def mark_paid(billing_id):
    billing = Billing.query.get_or_404(billing_id)
    amount = request.form.get('total_amount')
    if amount:
        billing.total_amount = float(amount)
    billing.payment_status = 'paid'
    db.session.commit()
    flash('Payment recorded successfully.', 'success')
    return redirect(url_for('pharmacy.billing_list'))