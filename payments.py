from flask import Blueprint, jsonify

payments_bp = Blueprint('payments', __name__)

@payments_bp.get('/status/<ticket_id>')
def payment_status(ticket_id):
    return jsonify({'message': f'Payment status for ticket {ticket_id} - coming soon'})

@payments_bp.post('/initiate/<ticket_id>')
def initiate_payment(ticket_id):
    return jsonify({'message': f'Payment initiation for ticket {ticket_id} - coming soon'})