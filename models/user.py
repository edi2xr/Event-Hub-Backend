from extension import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(120))
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default="user")
    is_active = db.Column(db.Boolean, default=True)
    club_name = db.Column(db.String(100))
    club_access_code = db.Column(db.String(10))
    leader_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    subscription_expires_at = db.Column(db.DateTime)
    club_id = db.Column(db.Integer, db.ForeignKey("clubs.id"))

    club = db.relationship("Club", back_populates="members")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @classmethod
    def get_user_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def get_user_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    @classmethod
    def get_leader_by_club_code(cls, code):
        return cls.query.filter_by(club_access_code=code, role="leader").first()

    def is_subscription_active(self):
        if not self.subscription_expires_at:
            return False
        return datetime.utcnow() < self.subscription_expires_at

    def activate_subscription(self):
        self.subscription_expires_at = datetime.utcnow() + timedelta(days=30)
        if not self.club_access_code:
            self.club_access_code = secrets.token_hex(4).upper()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "club_name": self.club_name,
            "club_access_code": self.club_access_code,
            "club_id": self.club_id
        }
