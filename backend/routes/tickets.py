from flask import Blueprint, request, jsonify
from database import db
from backend.models.models import Ticket, Payment, Event, PaymentStatus, TicketStatus
import random
import string

bp = Blueprint('tickets', __name__, url_prefix='/api/tickets')

def generate_ticket_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@bp.route('/generate', methods=['POST'])
def generate_tickets():
    data = request.get_json()
    payment_id = data.get('payment_id')
    
    payment = Payment.query.get(payment_id)
    if not payment:
        return jsonify({'error': 'Payment not found'}), 404
    
    if payment.status != PaymentStatus.COMPLETED:
        return jsonify({'error': 'Payment not completed'}), 400
    
    # Check if tickets already generated
    existing_tickets = Ticket.query.filter_by(payment_id=payment_id).count()
    if existing_tickets > 0:
        return jsonify({'error': 'Tickets already generated'}), 400
    
    # Generate tickets
    tickets = []
    for _ in range(payment.quantity):
        ticket_code = generate_ticket_code()
        while Ticket.query.filter_by(ticket_code=ticket_code).first():
            ticket_code = generate_ticket_code()
        
        ticket = Ticket(
            ticket_code=ticket_code,
            payment_id=payment.id,
            event_id=payment.event_id
        )
        db.session.add(ticket)
        tickets.append({
            'ticket_code': ticket_code,
            'event_id': payment.event_id
        })
    
    db.session.commit()
    
    return jsonify({
        'tickets': tickets,
        'message': f'{len(tickets)} tickets generated successfully'
    }), 201

@bp.route('/validate/<ticket_code>', methods=['GET'])
def validate_ticket(ticket_code):
    ticket = Ticket.query.filter_by(ticket_code=ticket_code).first()
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404
    
    event = Event.query.get(ticket.event_id)
    payment = Payment.query.get(ticket.payment_id)
    
    return jsonify({
        'ticket_code': ticket.ticket_code,
        'status': ticket.status.value,
        'event': {
            'id': event.id,
            'name': event.name,
            'date': event.date.isoformat(),
            'venue': event.venue
        },
        'payment_status': payment.status.value,
        'used_at': ticket.used_at.isoformat() if ticket.used_at else None
    })

@bp.route('/use/<ticket_code>', methods=['POST'])
def use_ticket(ticket_code):
    ticket = Ticket.query.filter_by(ticket_code=ticket_code).first()
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404
    
    if ticket.status != TicketStatus.ACTIVE:
        return jsonify({'error': 'Ticket already used or cancelled'}), 400
    
    ticket.status = TicketStatus.USED
    ticket.used_at = db.func.now()
    db.session.commit()
    
    return jsonify({'message': 'Ticket used successfully'})

@bp.route('/payment/<int:payment_id>', methods=['GET'])
def get_tickets_by_payment(payment_id):
    payment = Payment.query.get(payment_id)
    if not payment:
        return jsonify({'error': 'Payment not found'}), 404
    
    tickets = Ticket.query.filter_by(payment_id=payment_id).all()
    event = Event.query.get(payment.event_id)
    
    ticket_list = []
    for ticket in tickets:
        ticket_list.append({
            'ticket_code': ticket.ticket_code,
            'status': ticket.status.value,
            'created_at': ticket.created_at.isoformat(),
            'used_at': ticket.used_at.isoformat() if ticket.used_at else None
        })
    
    return jsonify({
        'payment_id': payment.id,
        'event': {
            'id': event.id,
            'name': event.name,
            'date': event.date.isoformat(),
            'venue': event.venue
        },
        'tickets': ticket_list,
        'total_amount': payment.amount
    })