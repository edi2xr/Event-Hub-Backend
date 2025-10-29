from extension import db
from uuid import uuid4
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
from enum import Enum

class UserRole(Enum):
    ADMIN = "admin"
    LEADER = "leader"
    USER = "user"

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.String(), primary_key=True, default=lambda: str(uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.Text(), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.USER, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)
    
    # Leader-specific fields
    club_name = db.Column(db.String(100), nullable=True)
    subscription_active = db.Column(db.Boolean, default=False)
    subscription_expires_at = db.Column(db.DateTime, nullable=True)
    club_access_code = db.Column(db.String(10), unique=True, nullable=True)
    
    # Relationships  
    leader_id = db.Column(db.String(), db.ForeignKey('users.id'), nullable=True)
    club_members = db.relationship('User', backref='leader', remote_side=[id], foreign_keys='User.leader_id', lazy='select')

    def __repr__(self):
        return f"<User {self.username} - {self.role.value}>"
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def is_subscription_active(self):
        if self.role != UserRole.LEADER:
            return False
        if not self.subscription_active or not self.subscription_expires_at:
            return False
        expires_at = self.subscription_expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return expires_at > datetime.now(timezone.utc)
    
    def activate_subscription(self, duration_days=30):
        self.subscription_active = True
        self.subscription_expires_at = datetime.now(timezone.utc) + timedelta(days=duration_days)
        if not self.club_access_code:
            self.club_access_code = self.generate_club_code()
    
    @staticmethod
    def generate_club_code():
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    def to_dict(self):
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role.value,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if self.role == UserRole.LEADER:
            data.update({
                'club_name': self.club_name,
                'subscription_active': self.is_subscription_active(),
                'club_access_code': self.club_access_code
            })
        
        return data
    
    @classmethod
    def get_user_by_username(cls, username):
        return cls.query.filter_by(username=username).first()
    
    @classmethod
    def get_user_by_email(cls, email):
        return cls.query.filter_by(email=email).first()
    
    @classmethod
    def get_leader_by_club_code(cls, club_code):
        if not club_code:
            return None
        return cls.query.filter_by(club_access_code=club_code, role=UserRole.LEADER).first()
    
    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
    
    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

class Club(db.Model):
    __tablename__ = "clubs"
    id = db.Column(db.String(), primary_key=True, default=lambda: str(uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text())
    leader_id = db.Column(db.String(), db.ForeignKey('users.id'), nullable=False)
    access_code = db.Column(db.String(10), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)
    
    leader = db.relationship('User', backref='led_club', foreign_keys=[leader_id])
    
    def to_dict(self):
        try:
            leader_name = self.leader.username if self.leader else None
        except Exception:
            leader_name = None
            
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'leader': leader_name,
            'access_code': self.access_code,
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
    
    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

class EventStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class Event(db.Model):
    __tablename__ = "events"
    id = db.Column(db.String(), primary_key=True, default=lambda: str(uuid4()))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text())
    event_date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    ticket_price = db.Column(db.Float, default=0.0)
    vip_price = db.Column(db.Float, nullable=True)
    vvip_price = db.Column(db.Float, nullable=True)
    max_attendees = db.Column(db.Integer, nullable=True)
    banner_url = db.Column(db.String(500), nullable=True)
    renewal_period = db.Column(db.String(20), default='monthly')
    status = db.Column(db.Enum(EventStatus), default=EventStatus.PENDING, nullable=False)
    
    leader_id = db.Column(db.String(), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    leader = db.relationship('User', backref='events', foreign_keys=[leader_id])
    tickets = db.relationship('Ticket', backref='event', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'event_date': self.event_date.isoformat() if self.event_date else None,
            'location': self.location,
            'ticket_price': self.ticket_price,
            'vip_price': self.vip_price,
            'vvip_price': self.vvip_price,
            'max_attendees': self.max_attendees,
            'banner_url': self.banner_url,
            'renewal_period': self.renewal_period,
            'status': self.status.value,
            'leader_id': self.leader_id,
            'leader_name': self.leader.username if self.leader else None,
            'club_name': self.leader.club_name if self.leader and self.leader.role == UserRole.LEADER else None,
            'tickets_sold': self.tickets.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
    
    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class Ticket(db.Model):
    __tablename__ = "tickets"
    id = db.Column(db.String(), primary_key=True, default=lambda: str(uuid4()))
    event_id = db.Column(db.String(), db.ForeignKey('events.id'), nullable=False)
    user_id = db.Column(db.String(), db.ForeignKey('users.id'), nullable=False)
    
    ticket_price = db.Column(db.Float, nullable=False)
    commission = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    
    payment_status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    mpesa_receipt = db.Column(db.String(100), nullable=True)
    payment_phone = db.Column(db.String(20), nullable=True)
    
    purchased_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = db.relationship('User', backref='tickets', foreign_keys=[user_id])
    
    @staticmethod
    def calculate_commission(price):
        return round(price * 0.05, 2)
    
    @staticmethod
    def calculate_total(price):
        commission = Ticket.calculate_commission(price)
        return round(price + commission, 2)
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'event_title': self.event.title if self.event else None,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'ticket_price': self.ticket_price,
            'commission': self.commission,
            'total_amount': self.total_amount,
            'payment_status': self.payment_status.value,
            'mpesa_receipt': self.mpesa_receipt,
            'purchased_at': self.purchased_at.isoformat() if self.purchased_at else None
        }
    
    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
    
    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e