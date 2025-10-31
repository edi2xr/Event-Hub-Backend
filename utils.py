from functools import wraps
from flask import jsonify, request
from extension import mail
from flask_mail import Message
from flask import current_app

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

def send_subscription_email(recipient_email, username):
    """
    Send a subscription success email to the user.

    Args:
        recipient_email (str): The recipient's email address.
        username (str): The username of the recipient.

    Returns:
        None
    """
    subject = "Subscription Successful"
    body = f"Hello {username},\n\nYour subscription was successful! Welcome to Event Hub.\n\nBest regards,\nEvent Hub Team"
    msg = Message(subject=subject, recipients=[recipient_email], body=body)
    with current_app.app_context():
        mail.send(msg)