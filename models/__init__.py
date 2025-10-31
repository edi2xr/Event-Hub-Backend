from enum import Enum
from .user import User
from .club import Club
from .event import Event
from .notification import Notification
from .audit import AuditLog

class UserRole(Enum):
    USER = "user"
    ADMIN = "admin"
    LEADER = "leader"
    CLUB_ADMIN = "club_admin"

class EventStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class Ticket:
    def __init__(self, id, event_id, user_id, price, status="pending"):
        self.id = id
        self.event_id = event_id
        self.user_id = user_id
        self.price = price
        self.status = status

__all__ = ['User', 'Club', 'Event', 'Notification', 'AuditLog', 'UserRole', 'EventStatus', 'PaymentStatus', 'Ticket']