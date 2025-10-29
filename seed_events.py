from app import app
from database import db
from backend.models.models import Event
from datetime import datetime, timedelta

def seed_events():
    with app.app_context():
        # Clear existing events
        Event.query.delete()
        
        # Sample events
        events = [
            Event(
                name="Tech Conference 2024",
                description="Annual technology conference featuring latest innovations",
                date=datetime.now() + timedelta(days=30),
                venue="Nairobi Convention Center",
                price=2500.0,
                total_tickets=500,
                available_tickets=500,
                owner_phone="254712345678"
            ),
            Event(
                name="Music Festival",
                description="Three-day music festival with top artists",
                date=datetime.now() + timedelta(days=45),
                venue="Uhuru Gardens",
                price=1500.0,
                total_tickets=1000,
                available_tickets=1000,
                owner_phone="254712345678"
            ),
            Event(
                name="Business Summit",
                description="Networking event for entrepreneurs and business leaders",
                date=datetime.now() + timedelta(days=15),
                venue="KICC",
                price=3000.0,
                total_tickets=200,
                available_tickets=200,
                owner_phone="254712345678"
            )
        ]
        
        for event in events:
            db.session.add(event)
        
        db.session.commit()
        print(f"Seeded {len(events)} events successfully!")

if __name__ == '__main__':
    seed_events()