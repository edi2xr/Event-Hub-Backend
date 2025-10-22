from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta, timezone
from extension import db, jwt, migrate
from auth import auth_bp
from models import User, UserRole

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
    
    
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    CORS(app,origins=["http://localhost:5173", "http://127.0.0.1:5000"], supports_credentials=True)
    
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired'}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Invalid token'}), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'error': 'Authorization token is required'}), 401
    
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    @app.route("/")
    def home():
        return jsonify({
            "message": "Event Hub API is running",
            "version": "1.0.0",
            "endpoints": {
                "auth": "/api/auth",
                "signup": "/api/auth/signup",
                "login": "/api/auth/login",
                "profile": "/api/auth/profile",
                "subscribe": "/api/auth/subscribe"
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
    app.run(debug=False, port=5000)