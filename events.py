from flask import Blueprint, jsonify, request
from models import Event, EventStatus, User, UserRole, Ticket, PaymentStatus
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from functools import wraps
from datetime import datetime, timezone
from utils import validate_json_input
from auth import role_required

events_bp = Blueprint('events', __name__)

@events_bp.post('/create')
@role_required(UserRole.LEADER)
def create_event():
    current_user_id = get_jwt_identity()
    leader = User.query.get(current_user_id)
    
    if not leader.is_subscription_active():
        return jsonify({'error': 'Active subscription required to create events'}), 403
    
    data = request.get_json()
    
    if not data.get('title') or not data.get('event_date'):
        return jsonify({'error': 'Title and event date are required'}), 400
    
    try:
        event_date = datetime.fromisoformat(data['event_date'].replace('Z', '+00:00'))
        if event_date.tzinfo is None:
            event_date = event_date.replace(tzinfo=timezone.utc)
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    if event_date < datetime.now(timezone.utc):
        return jsonify({'error': 'Event date must be in the future'}), 400
    
    new_event = Event(
        title=data['title'],
        description=data.get('description'),
        event_date=event_date,
        location=data.get('location'),
        ticket_price=max(0, float(data.get('ticket_price', 0))),
        vip_price=max(0, float(data.get('vip_price'))) if data.get('vip_price') else None,
        vvip_price=max(0, float(data.get('vvip_price'))) if data.get('vvip_price') else None,
        max_attendees=data.get('max_attendees'),
        banner_url=data.get('banner_url'),
        renewal_period=data.get('renewal_period', 'monthly'),
        leader_id=leader.id,
        status=EventStatus.PENDING
    )
    
    try:
        new_event.save()
        return jsonify({
            'message': 'Event created successfully and pending admin approval',
            'event': new_event.to_dict()
        }), 201
    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to create event'}), 500

@events_bp.get('/public')
def get_public_events():
    """Public endpoint for approved events - no authentication required"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = Event.query.filter_by(status=EventStatus.APPROVED)
    
    paginated = query.order_by(Event.event_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    events_data = []
    for event in paginated.items:
        event_dict = event.to_dict()
        # Add club access code for join functionality
        if event.leader and event.leader.club_access_code:
            event_dict['club_access_code'] = event.leader.club_access_code
        events_data.append(event_dict)
    
    return jsonify({
        'events': events_data,
        'total': paginated.total,
        'page': paginated.page,
        'per_page': paginated.per_page,
        'pages': paginated.pages
    }), 200

@events_bp.get('/all')
@jwt_required()
def get_all_events():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status', None)
    
    query = Event.query
    
    if user.role == UserRole.USER:
        # Show all approved events for users
        query = query.filter_by(status=EventStatus.APPROVED)
    elif user.role == UserRole.LEADER:
        query = query.filter_by(leader_id=user.id)
    
    if status and user.role != UserRole.USER:
        try:
            query = query.filter_by(status=EventStatus(status))
        except ValueError:
            return jsonify({'error': 'Invalid status'}), 400
    
    paginated = query.order_by(Event.event_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    events_data = []
    for event in paginated.items:
        event_dict = event.to_dict()
        # Add club access code for join functionality
        if event.leader and event.leader.club_access_code:
            event_dict['club_access_code'] = event.leader.club_access_code
        events_data.append(event_dict)
    
    return jsonify({
        'events': events_data,
        'total': paginated.total,
        'page': paginated.page,
        'per_page': paginated.per_page,
        'pages': paginated.pages
    }), 200

@events_bp.get('/<event_id>')
@jwt_required()
def get_event(event_id):
    event = Event.query.get(event_id)
    
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    return jsonify({'event': event.to_dict()}), 200

@events_bp.patch('/<event_id>')
@role_required(UserRole.LEADER)
def update_event(event_id):
    current_user_id = get_jwt_identity()
    event = Event.query.get(event_id)
    
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    if event.leader_id != current_user_id:
        return jsonify({'error': 'You can only update your own events'}), 403
    
    data = request.get_json()
    
    if 'title' in data:
        event.title = data['title']
    if 'description' in data:
        event.description = data['description']
    if 'event_date' in data:
        try:
            event_date = datetime.fromisoformat(data['event_date'].replace('Z', '+00:00'))
            if event_date < datetime.now(timezone.utc):
                return jsonify({'error': 'Event date must be in the future'}), 400
            event.event_date = event_date
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
    if 'location' in data:
        event.location = data['location']
    if 'ticket_price' in data:
        event.ticket_price = float(data['ticket_price'])
    if 'max_attendees' in data:
        event.max_attendees = data['max_attendees']
    if 'banner_url' in data:
        event.banner_url = data['banner_url']
    
    try:
        event.save()
        return jsonify({
            'message': 'Event updated successfully',
            'event': event.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to update event'}), 500

@events_bp.delete('/<event_id>')
@role_required(UserRole.LEADER)
def delete_event(event_id):
    current_user_id = get_jwt_identity()
    event = Event.query.get(event_id)
    
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    if event.leader_id != current_user_id:
        return jsonify({'error': 'You can only delete your own events'}), 403
    
    try:
        event.delete()
        return jsonify({'message': 'Event deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to delete event'}), 500

@events_bp.patch('/<event_id>/approve')
@role_required(UserRole.ADMIN)
def approve_event(event_id):
    event = Event.query.get(event_id)
    
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    event.status = EventStatus.APPROVED
    
    try:
        event.save()
        return jsonify({
            'message': 'Event approved successfully',
            'event': event.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to approve event'}), 500

@events_bp.patch('/<event_id>/reject')
@role_required(UserRole.ADMIN)
def reject_event(event_id):
    event = Event.query.get(event_id)
    
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    event.status = EventStatus.REJECTED
    
    try:
        event.save()
        return jsonify({
            'message': 'Event rejected',
            'event': event.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to reject event'}), 500

@events_bp.post('/<event_id>/purchase-ticket')
@role_required(UserRole.USER)
def purchase_ticket(event_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    event = Event.query.get(event_id)
    
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    if event.status != EventStatus.APPROVED:
        return jsonify({'error': 'Event is not available for ticket purchase'}), 400
    
    if user.leader_id != event.leader_id:
        return jsonify({'error': 'You can only purchase tickets for events in your club'}), 403
    
    leader = User.query.get(event.leader_id)
    if not leader or not leader.is_subscription_active():
        return jsonify({'error': 'Event organizer subscription is inactive'}), 403
    
    existing_ticket = Ticket.query.filter_by(event_id=event_id, user_id=current_user_id).first()
    if existing_ticket:
        return jsonify({'error': 'You already have a ticket for this event'}), 400
    
    if event.max_attendees:
        current_tickets = event.tickets.count()
        if current_tickets >= event.max_attendees:
            return jsonify({'error': 'Event is sold out'}), 400
    
    data = request.get_json()
    phone_number = data.get('phone_number')
    
    if not phone_number:
        return jsonify({'error': 'Phone number is required for M-Pesa payment'}), 400
    
    commission = Ticket.calculate_commission(event.ticket_price)
    total_amount = Ticket.calculate_total(event.ticket_price)
    
    new_ticket = Ticket(
        event_id=event.id,
        user_id=current_user_id,
        ticket_price=event.ticket_price,
        commission=commission,
        total_amount=total_amount,
        payment_status=PaymentStatus.PENDING,
        payment_phone=phone_number
    )
    
    try:
        new_ticket.save()
        
        return jsonify({
            'message': 'Ticket created successfully. Use the payment endpoint to complete purchase',
            'ticket': new_ticket.to_dict(),
            'next_step': {
                'endpoint': f'/api/payments/initiate/{new_ticket.id}',
                'method': 'POST',
                'description': 'Call this endpoint to initiate M-Pesa payment'
            }
        }), 201
    except Exception as e:
        return jsonify({'error': 'Failed to create ticket'}), 500

@events_bp.get('/my-tickets')
@role_required(UserRole.USER)
def get_my_tickets():
    current_user_id = get_jwt_identity()
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    paginated = Ticket.query.filter_by(user_id=current_user_id).order_by(
        Ticket.purchased_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'tickets': [ticket.to_dict() for ticket in paginated.items],
        'total': paginated.total,
        'page': paginated.page,
        'per_page': paginated.per_page,
        'pages': paginated.pages
    }), 200

@events_bp.get('/<event_id>/tickets')
@role_required(UserRole.LEADER)
def get_event_tickets(event_id):
    current_user_id = get_jwt_identity()
    event = Event.query.get(event_id)
    
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    if event.leader_id != current_user_id:
        return jsonify({'error': 'You can only view tickets for your own events'}), 403
    
    tickets = Ticket.query.filter_by(event_id=event_id).all()
    
    return jsonify({
        'event_title': event.title,
        'tickets': [ticket.to_dict() for ticket in tickets],
        'total_tickets': len(tickets),
        'total_revenue': sum(ticket.ticket_price for ticket in tickets if ticket.payment_status == PaymentStatus.COMPLETED),
        'total_commission': sum(ticket.commission for ticket in tickets if ticket.payment_status == PaymentStatus.COMPLETED)
    }), 200

