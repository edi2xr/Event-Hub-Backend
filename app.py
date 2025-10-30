from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta, timezone
from extension import db, jwt, migrate
from auth import auth_bp
from events import events_bp
from payments import payments_bp
from club_payments import club_bp
from debug_events import debug_bp
from models import User, UserRole
from flask_migrate import upgrade


load_dotenv()



def create_app():
    app = Flask(__name__)
    
    
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    jwt_secret = os.getenv("JWT_SECRET_KEY")
    if not jwt_secret:
        raise ValueError("JWT_SECRET_KEY environment variable is required")
    app.config["JWT_SECRET_KEY"] = jwt_secret
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=7)
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False
    app.config["JWT_ACCESS_COOKIE_NAME"] = "access_token"
    app.config["JWT_REFRESH_COOKIE_NAME"] = "refresh_token"
    app.config["JWT_COOKIE_SAMESITE"] = "None"
    app.config["JWT_COOKIE_SECURE"] = True
    app.config["JWT_COOKIE_PATH"] = "/"
    app.config["JWT_SESSION_COOKIE"] = False
    
    
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    with app.app_context():
        upgrade()

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(events_bp, url_prefix='/api/events')
    app.register_blueprint(payments_bp, url_prefix='/api/payments')
    app.register_blueprint(club_bp, url_prefix='/api')
    app.register_blueprint(debug_bp, url_prefix='/api/debug')
    
    CORS(app,support_credentials=True)
    
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired'}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Invalid token'}), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'error': 'Authorization token is required'}), 401
    
    
    
    
    @app.route("/")
    def home():
        return jsonify({
            "message": "Event Hub API is running",
            "version": "1.0.0",
            "endpoints": {
                "auth": "/api/auth",
                "events": "/api/events",
                "signup": "/api/auth/signup",
                "login": "/api/auth/login",
                "profile": "/api/auth/profile",
                "subscribe": "/api/auth/subscribe",
                "create_event": "/api/events/create",
                "all_events": "/api/events/all",
                "purchase_ticket": "/api/events/<event_id>/purchase-ticket",
                "initiate_payment": "/api/payments/initiate/<ticket_id>",
                "payment_status": "/api/payments/status/<ticket_id>"
            }
        })
    
    @app.route("/api/health")
    def health_check():
        try:
            
            db.session.execute(db.text('SELECT 1'))
            return jsonify({"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()})
        except Exception as e:
            return jsonify({"status": "unhealthy", "error": "Database connection failed"}), 503
    
    return app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
        
        try:
            admin = User.get_user_by_username('admin')
            if not admin:
                admin_password = os.getenv('ADMIN_PASSWORD')
                if admin_password:
                    admin = User(
                        username=os.getenv('ADMIN_USERNAME', 'admin'),
                        email=os.getenv('ADMIN_EMAIL', 'admin@eventhub.com'),
                        role=UserRole.ADMIN
                    )
                    admin.set_password(admin_password)
                    admin.save()
                    print("Default admin user created")
        except Exception as e:
            print(f"Error creating admin user: {e}")
    app.run(debug=True, port=8000, host="0.0.0.0")