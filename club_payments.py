from flask import Blueprint, jsonify

club_bp = Blueprint('club', __name__)

@club_bp.get('/clubs')
def get_clubs():
    return jsonify({'clubs': [], 'message': 'Clubs endpoint working'})