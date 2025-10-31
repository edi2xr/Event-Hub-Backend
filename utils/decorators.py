from functools import wraps
from flask import request, jsonify
import jwt
from extensions import db
from models.user import User

SECRET_KEY = "your-secret-key"  # 🔐 Change this to a strong secret or load from environment variable

def token_required(f):
    """Decorator to ensure JWT token validity."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # JWT expected in Authorization header
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = User.query.get(data["id"])
            if not current_user:
                return jsonify({"error": "User not found"}), 404
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(current_user, *args, **kwargs)
    return decorated


def admin_only(f):
    """Decorator to ensure the user is an admin."""
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user.role != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(current_user, *args, **kwargs)
    return decorated
