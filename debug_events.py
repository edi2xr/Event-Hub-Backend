from flask import Blueprint, jsonify
from models import Event, EventStatus

debug_bp = Blueprint('debug', __name__)

@debug_bp.get('/test-events')
def test_events():
    events = Event.query.filter_by(status=EventStatus.PENDING).all()
    return jsonify({
        'total_events': len(events),
        'events': [{'id': e.id, 'title': e.title, 'status': e.status.value} for e in events]
    })

@debug_bp.post('/approve-event/<event_id>')
def approve_event_simple(event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    event.status = EventStatus.APPROVED
    event.save()
    return jsonify({'message': f'Event {event.title} approved successfully'})

@debug_bp.get('/admin-panel')
def admin_panel():
    events = Event.query.filter_by(status=EventStatus.PENDING).all()
    html = '<h1>Admin Panel - Pending Events</h1>'
    
    if not events:
        html += '<p>No pending events</p>'
    else:
        for event in events:
            html += f'''
            <div style="border: 1px solid #ccc; margin: 10px; padding: 10px;">
                <h3>{event.title}</h3>
                <p>Status: {event.status.value}</p>
                <p>Leader: {event.leader.username if event.leader else "Unknown"}</p>
                <button onclick="approveEvent('{event.id}')">Approve</button>
            </div>
            '''
    
    html += '''
    <script>
    function approveEvent(eventId) {
        fetch(`/api/debug/approve-event/${eventId}`, {method: 'POST'})
        .then(r => r.json())
        .then(data => {
            alert(data.message);
            location.reload();
        });
    }
    </script>
    '''
    
    return html