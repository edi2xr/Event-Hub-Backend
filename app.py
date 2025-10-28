from flask import Flask
from extensions import db, migrate, jwt, cors
from API.admin import admin_bp
import models  # ensures models are registered with SQLAlchemy

def create_app():
    app = Flask(__name__)

    # Basic configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eventhub.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'super-secret-key'  # change this later

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)

    # Register blueprints
    app.register_blueprint(admin_bp, url_prefix='/admin')

    @app.route('/')
    def home():
        return {"message": "Welcome to Event Hub API 🎉"}

    return app


# Entry point
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
