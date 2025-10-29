from flask import Blueprint, jsonify, request
from backend.models.models import Event
from database import db
from datetime import datetime

bp = Blueprint('events', __name__, url_prefix='/api')

@bp.route('/events', methods=['GET'])
def get_events():
    events = Event.query.all()
    event_list = []
    
    for event in events:
        event_list.append({
            'id': event.id,
            'title': event.name,
            'description': event.description,
            'date': event.date.isoformat(),
            'location': event.venue,
            'price': event.price
        })
    
    return jsonify(event_list)

@bp.route('/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    return jsonify({
        'id': event.id,
        'title': event.name,
        'description': event.description,
        'date': event.date.isoformat(),
        'location': event.venue,
        'price': event.price
    })

@bp.route('/events', methods=['POST'])
def create_event():
    data = request.get_json()
    
    if not data or not all(k in data for k in ['title', 'date', 'location', 'owner_phone']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        event = Event(
            name=data['title'],
            description=data.get('description', ''),
            date=datetime.fromisoformat(data['date']),
            venue=data['location'],
            price=float(data.get('price', 1000)),
            total_tickets=100,
            available_tickets=100,
            owner_phone=data['owner_phone']
        )
        
        db.session.add(event)
        db.session.commit()
        
        return jsonify({
            'id': event.id,
            'title': event.name,
            'description': event.description,
            'date': event.date.isoformat(),
            'location': event.venue,
            'price': event.price,
            'owner_phone': event.owner_phone
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create event'}), 500

@bp.route('/events/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    data = request.get_json()
    event = Event.query.get(event_id)
    
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    # Verify ownership
    if data.get('owner_phone') != event.owner_phone:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        if 'title' in data:
            event.name = data['title']
        if 'description' in data:
            event.description = data['description']
        if 'date' in data:
            event.date = datetime.fromisoformat(data['date'])
        if 'location' in data:
            event.venue = data['location']
        if 'price' in data:
            event.price = data['price']
        
        db.session.commit()
        
        return jsonify({
            'id': event.id,
            'title': event.name,
            'description': event.description,
            'date': event.date.isoformat(),
            'location': event.venue,
            'price': event.price,
            'owner_phone': event.owner_phone
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update event'}), 500