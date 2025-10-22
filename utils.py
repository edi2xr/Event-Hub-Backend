# Input validation utilities for Event Hub Backend
# This module provides validation functions for user input data

import re
from functools import wraps
from flask import jsonify, request

def validate_email(email):
    """
    Validate email format using regex pattern.
    
    Args:
        email (str): Email address to validate
        
    Returns:
        bool: True if email format is valid, False otherwise
        
    Example:
        >>> validate_email("user@example.com")
        True
        >>> validate_email("invalid-email")
        False
    """
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """
    Validate password strength requirements.
    
    Password must:
    - Be at least 8 characters long
    - Contain at least one letter
    - Contain at least one number
    
    Args:
        password (str): Password to validate
        
    Returns:
        tuple: (is_valid: bool, message: str)
        
    Example:
        >>> validate_password("Password123")
        (True, "Valid password")
        >>> validate_password("weak")
        (False, "Password must be at least 8 characters long")
    """

    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    

    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter"
    
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, "Valid password"

def validate_username(username):
    """
    Validate username format and length.
    
    Username must:
    - Be between 3 and 20 characters
    - Only contain letters, numbers, and underscores
    
    Args:
        username (str): Username to validate
        
    Returns:
        tuple: (is_valid: bool, message: str)
        
    Example:
        >>> validate_username("user123")
        (True, "Valid username")
        >>> validate_username("ab")
        (False, "Username must be between 3 and 20 characters")
    """
    
    if len(username) < 3 or len(username) > 20:
        return False, "Username must be between 3 and 20 characters"
    
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    
    return True, "Valid username"

def validate_json_input(required_fields=None):
    """
    Decorator to validate JSON input for Flask routes.
    
    Validates:
    - Request has JSON content type
    - Request body contains valid JSON
    - All required fields are present and not empty
    
    Args:
        required_fields (list, optional): List of field names that must be present
        
    Returns:
        function: Decorated function with input validation
        
    Example:
        @validate_json_input(['username', 'email'])
        def create_user():
            # This function will only run if username and email are provided
            pass
    """
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