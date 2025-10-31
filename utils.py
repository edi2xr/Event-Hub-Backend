from functools import wraps
from flask import jsonify, request

def validate_json_input(required_fields=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Missing JSON data'}), 400
            
            if required_fields:
                for field in required_fields:
                    if not data.get(field):
                        return jsonify({'error': f'{field} is required'}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator