from flask import Blueprint, jsonify, request, make_response
from models import User, UserRole, Club
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required, 
    get_jwt_identity, get_jwt, set_access_cookies, set_refresh_cookies,
    unset_jwt_cookies
)
from functools import wraps
from datetime import datetime
from utils import validate_email, validate_password, validate_username, validate_json_input, send_subscription_email
import requests

auth_bp = Blueprint('auth', __name__)

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user or user.role not in allowed_roles:
                return jsonify({'error': 'Access denied'}), 403
            
            if user.role == UserRole.LEADER and not user.is_subscription_active():
                return jsonify({'error': 'Subscription expired. Please renew to continue.'}), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.post('/signup')
@validate_json_input(['username', 'email', 'password', 'role'])
def register_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not validate_email(data.get('email')):
        return jsonify({'error': 'Invalid email format'}), 400
    
    is_valid, message = validate_username(data.get('username'))
    if not is_valid:
        return jsonify({'error': message}), 400
    
    is_valid, message = validate_password(data.get('password'))
    if not is_valid:
        return jsonify({'error': message}), 400
    
    if User.get_user_by_username(data.get('username')):
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.get_user_by_email(data.get('email')):
        return jsonify({'error': 'Email already exists'}), 400
    
    try:
        role = UserRole(data.get('role'))
    except ValueError:
        return jsonify({'error': 'Invalid role. Must be admin, leader, or user'}), 400
    
    new_user = User(
        username=data.get('username'),
        email=data.get('email'),
        role=role
    )
    
    if role == UserRole.LEADER:
        if not data.get('club_name'):
            return jsonify({'error': 'Club name is required for leaders'}), 400
        new_user.club_name = data.get('club_name')
    
    if role == UserRole.USER and data.get('club_access_code'):
        leader = User.get_leader_by_club_code(data.get('club_access_code'))
        if not leader or not leader.is_subscription_active():
            return jsonify({'error': 'Invalid or inactive club access code'}), 400
        new_user.leader_id = leader.id
    
    try:
        new_user.set_password(data.get('password'))
        new_user.save()
    except Exception as e:
        return jsonify({'error': 'Failed to create user'}), 500
    
    return jsonify({
        'message': 'User created successfully',
        'user': new_user.to_dict()
    }), 201

@auth_bp.post('/login')
@validate_json_input(['username', 'password'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    is_valid, message = validate_username(username)
    if not is_valid:
        return jsonify({'error': message}), 400
    
    user = User.get_user_by_username(username)
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401

    if not user.is_active:
        return jsonify({'error': 'Account deactivated'}), 403

    additional_claims = {
        'role': user.role.value,
        'user_id': user.id,
        'subscription_active': user.is_subscription_active() if user.role == UserRole.LEADER else None
    }

    access_token = create_access_token(identity=user.id, additional_claims=additional_claims)
    refresh_token = create_refresh_token(identity=user.id)

    response = make_response(jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
    }))

    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)

    return response

@auth_bp.post('/logout')
def logout():
    response = make_response(jsonify({'message': 'Logged out successfully'}))
    unset_jwt_cookies(response)
    return response

@auth_bp.post('/refresh')
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    additional_claims = {
        'role': user.role.value,
        'user_id': user.id,
        'subscription_active': user.is_subscription_active() if user.role == UserRole.LEADER else None
    }
    
    new_access_token = create_access_token(
        identity=current_user_id,
        additional_claims=additional_claims
    )
    
    response = make_response(jsonify({'message': 'Token refreshed successfully'}))
    set_access_cookies(response, new_access_token)
    
    return response, 200

@auth_bp.get('/profile')
@jwt_required()
def get_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()}), 200

@auth_bp.post('/subscribe')
@jwt_required()
def subscribe_leader():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user.role != UserRole.LEADER:
        return jsonify({'error': 'Only leaders can subscribe'}), 403
    
    try:
        user.activate_subscription()
        user.save()

        # Send confirmation email
        send_subscription_email(user.email, user.club_name, user.subscription_expires_at)

    except Exception as e:
        return jsonify({'error': 'Failed to activate subscription'}), 500

    return jsonify({
        'message': 'Subscription activated successfully',
        'club_access_code': user.club_access_code,
        'expires_at': user.subscription_expires_at.isoformat()
    }), 200

@auth_bp.get('/club-members')
@role_required(UserRole.LEADER)
def get_club_members():
    current_user_id = get_jwt_identity()
    leader = User.query.get(current_user_id)
    
    if not leader:
        return jsonify({'error': 'Leader not found'}), 404
    
    try:
        members = User.query.filter_by(leader_id=leader.id).all()
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve club members'}), 500
    
    return jsonify({
        'club_name': leader.club_name,
        'access_code': leader.club_access_code,
        'members': [member.to_dict() for member in members]
    }), 200

@auth_bp.get('/users')
@role_required(UserRole.ADMIN)
def get_all_users():
    try:
        users = User.query.all()
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve users'}), 500
    return jsonify({
        'users': [user.to_dict() for user in users]
    }), 200

@auth_bp.patch('/users/<user_id>/toggle-status')
@role_required(UserRole.ADMIN)
def toggle_user_status(user_id):
    if not user_id or not user_id.strip() or '/' in user_id or '\\' in user_id:
        return jsonify({'error': 'Invalid user ID'}), 400
        
    try:
        user = User.query.get(user_id)
    except Exception as e:
        return jsonify({'error': 'Database error'}), 500
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        user.is_active = not user.is_active
        user.save()
    except Exception as e:
        return jsonify({'error': 'Failed to update user status'}), 500
    
    return jsonify({
        'message': f'User {"activated" if user.is_active else "deactivated"} successfully',
        'user': user.to_dict()
    }), 200

@auth_bp.post('/google-auth')
@validate_json_input(['id_token'])
def google_auth():
    data = request.get_json()
    id_token = data.get('id_token')
    
    if not id_token:
        return jsonify({'error': 'ID token is required'}), 400
    
    try:
        import base64
        import json
        import time
        
        try:
            parts = id_token.split('.')
            if len(parts) != 3:
                return jsonify({'error': 'Invalid Google token format'}), 401
            
            payload = parts[1]
            payload += '=' * (4 - len(payload) % 4)
            decoded_payload = base64.urlsafe_b64decode(payload)
            google_data = json.loads(decoded_payload)
            
            google_id = google_data.get('sub')
            email = google_data.get('email')
            name = google_data.get('name')
            picture = google_data.get('picture')
            
            if not email:
                return jsonify({'error': 'Email not provided by Google'}), 400
            
            exp = google_data.get('exp')
            if exp and exp < time.time():
                return jsonify({'error': 'Google token expired'}), 401
                
        except Exception as decode_error:
            return jsonify({'error': 'Invalid Google token'}), 401
        
        
        user = User.get_user_by_email(email)
        
        if not user:
            username = email.split('@')[0]
            original_username = username
            counter = 1
            while User.get_user_by_username(username):
                username = f"{original_username}{counter}"
                counter += 1
            
            user = User(
                username=username,
                email=email,
                role=UserRole.USER
            )
            user.set_password(f"google_{google_id}")
            user.save()
        
        if not user.is_active:
            return jsonify({'error': 'Account deactivated'}), 403
        
        additional_claims = {
            'role': user.role.value,
            'user_id': user.id,
            'subscription_active': user.is_subscription_active() if user.role == UserRole.LEADER else None
        }
        
        access_token = create_access_token(identity=user.id, additional_claims=additional_claims)
        refresh_token = create_refresh_token(identity=user.id)
        
        response = make_response(jsonify({
            'message': 'Google authentication successful',
            'user': user.to_dict(),
        }))
        
        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)
        
        return response
        
    except requests.RequestException:
        return jsonify({'error': 'Failed to verify Google token'}), 500
    except Exception as e:
        return jsonify({'error': 'Authentication failed'}), 500
