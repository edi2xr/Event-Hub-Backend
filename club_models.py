from extension import db
from uuid import uuid4
from datetime import datetime, timezone
from enum import Enum

class ClubSubscription(db.Model):
    __tablename__ = "club_subscriptions"
    id = db.Column(db.String(), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.String(), db.ForeignKey('users.id'), nullable=False)
    club_access_code = db.Column(db.String(10), nullable=False)
    club_name = db.Column(db.String(100), nullable=False)
    
    subscription_fee = db.Column(db.Float, default=200.0)
    platform_commission = db.Column(db.Float, default=20.0)
    total_amount = db.Column(db.Float, default=220.0)
    
    renewal_period = db.Column(db.String(20), default='monthly')  # weekly, monthly, quarterly, yearly
    payment_status = db.Column(db.String(20), default='completed')
    mpesa_receipt = db.Column(db.String(100), nullable=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    user = db.relationship('User', backref='club_subscriptions', foreign_keys=[user_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'club_access_code': self.club_access_code,
            'club_name': self.club_name,
            'subscription_fee': self.subscription_fee,
            'platform_commission': self.platform_commission,
            'total_amount': self.total_amount,
            'renewal_period': self.renewal_period,
            'payment_status': self.payment_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }
    
    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

class LuckyWinner(db.Model):
    __tablename__ = "lucky_winners"
    id = db.Column(db.String(), primary_key=True, default=lambda: str(uuid4()))
    event_id = db.Column(db.String(), db.ForeignKey('events.id'), nullable=False)
    user_id = db.Column(db.String(), db.ForeignKey('users.id'), nullable=False)
    ticket_id = db.Column(db.String(), nullable=True)  # Removed FK constraint temporarily
    
    selected_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    ticket_sent = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref='lucky_wins', foreign_keys=[user_id])
    event = db.relationship('Event', backref='lucky_winners', foreign_keys=[event_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'selected_at': self.selected_at.isoformat() if self.selected_at else None,
            'ticket_sent': self.ticket_sent
        }
    
    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e