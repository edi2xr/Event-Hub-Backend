from flask import Blueprint, jsonify
from backend.models.models import Event

bp = Blueprint('events', __name__, url_prefix='/api/events')

@bp.route('/', methods=['GET'])
def get_events():
    events = Event.query.all()
    event_list = []
    
    for event in events:
        event_list.append({
            'id': event.id,
            'name': event.name,
            'description': event.description,
            'date': event.date.isoformat(),
            'venue': event.venue,
            'price': event.price,
            'total_tickets': event.total_tickets,
            'available_tickets': event.available_tickets
        })
    
    return jsonify({'events': event_list})

@bp.route('/<int:event_id>', methods=['GET'])
def get_event(event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    return jsonify({
        'id': event.id,
        'name': event.name,
        'description': event.description,
        'date': event.date.isoformat(),
        'venue': event.venue,
        'price': event.price,
        'total_tickets': event.total_tickets,
        'available_tickets': event.available_tickets
    })