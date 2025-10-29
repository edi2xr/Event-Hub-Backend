from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from database import db
import os

app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///eventhub.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

db.init_app(app)
migrate = Migrate(app, db)

# Import models after db is initialized
from backend.models.models import Event, Payment, Ticket

# Import and register routes
from backend.routes import payments, tickets, events
app.register_blueprint(payments.bp)
app.register_blueprint(tickets.bp)
app.register_blueprint(events.bp)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8000)