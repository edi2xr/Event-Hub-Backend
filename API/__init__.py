from flask import Blueprint

api_bp = Blueprint("api", __name__)

@api_bp.route("/")
def home():
    return {"message": "Welcome to the Event Hub API!"}, 200
