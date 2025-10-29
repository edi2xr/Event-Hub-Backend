from flask import Blueprint, request, jsonify
from models import User, Event
from club_models import ClubSubscription, LuckyWinner
from flask_jwt_extended import jwt_required, get_jwt_identity
from extension import db
import random

club_bp = Blueprint('club', __name__)

@club_bp.post('/payments/club-subscription')
def club_subscription_payment():
    data = request.get_json()
    phone_number = data.get('phone_number')
    club_access_code = data.get('club_access_code')
    amount = data.get('amount', 220)
    
    if not phone_number or not club_access_code:
        return jsonify({'error': 'Phone number and club access code required'}), 400
    
    # Find club leader
    leader = User.get_leader_by_club_code(club_access_code)
    if not leader:
        return jsonify({'error': 'Invalid club access code'}), 404
    
    try:
        # Simulate M-Pesa payment (replace with actual M-Pesa integration)
        return jsonify({
            'message': 'Club subscription payment initiated',
            'checkout_request_id': f'ws_CO_{random.randint(100000, 999999)}',
            'club_name': leader.club_name
        }), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@club_bp.get('/user/subscriptions')
@jwt_required()
def get_user_subscriptions():
    current_user_id = get_jwt_identity()
    
    subscriptions = ClubSubscription.query.filter_by(
        user_id=current_user_id, 
        is_active=True
    ).all()
    
    return jsonify({
        'subscriptions': [sub.to_dict() for sub in subscriptions]
    }), 200

@club_bp.post('/events/<event_id>/pick-winners')
@jwt_required()
def pick_lucky_winners(event_id):
    current_user_id = get_jwt_identity()
    data = request.get_json()
    num_winners = data.get('num_winners', 1)
    
    # Verify event ownership
    event = Event.query.get(event_id)
    if not event or event.leader_id != current_user_id:
        return jsonify({'error': 'Event not found or unauthorized'}), 404
    
    # Get club members (users subscribed to this club)
    leader = User.query.get(current_user_id)
    if not leader or not leader.club_access_code:
        return jsonify({'error': 'Club access code not found'}), 400
    
    club_members = ClubSubscription.query.filter_by(
        club_access_code=leader.club_access_code,
        is_active=True
    ).all()
    
    if len(club_members) < num_winners:
        return jsonify({'error': f'Not enough club members. Only {len(club_members)} available'}), 400
    
    # Randomly select winners
    selected_members = random.sample(club_members, min(num_winners, len(club_members)))
    winners = []
    
    try:
        for member in selected_members:
            # Create lucky winner record
            winner = LuckyWinner(
                event_id=event_id,
                user_id=member.user_id,
                ticket_sent=True
            )
            winner.save()
            
            winners.append({
                'id': winner.id,
                'username': member.user.username if member.user else 'Unknown',
                'user_id': member.user_id
            })
        
        return jsonify({
            'message': f'{len(winners)} lucky winners selected',
            'winners': winners
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500