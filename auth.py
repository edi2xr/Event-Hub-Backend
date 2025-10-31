from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import User, UserRole
from utils import validate_json_input

auth_bp = Blueprint('auth', __name__)

@auth_bp.post('/signup')
@validate_json_input(['username', 'email', 'password'])
def register_user():
    data = request.get_json()
    
    if User.get_user_by_username(data.get('username')):
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.get_user_by_email(data.get('email')):
        return jsonify({'error': 'Email already exists'}), 400
    
    user = User(
        username=data.get('username'),
        email=data.get('email'),
        role=data.get('role', 'user')
    )
    user.set_password(data.get('password'))
    user.save()
    
    return jsonify({
        'message': 'User created successfully',
        'user': user.to_dict()
    }), 201

@auth_bp.post('/login')
@validate_json_input(['username', 'password'])
def login():
    data = request.get_json()
    user = User.get_user_by_username(data.get('username'))
    
    if not user or not user.check_password(data.get('password')):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account deactivated'}), 403
    
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'user': user.to_dict()
    })

@auth_bp.get('/profile')
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()})