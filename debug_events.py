from flask import Blueprint, jsonify

debug_bp = Blueprint('debug', __name__)

@debug_bp.get('/info')
def debug_info():
    return jsonify({'message': 'Debug endpoint working', 'status': 'ok'})