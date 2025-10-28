from datetime import datetime
from extensions import db

class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(50), nullable=False)
    target_table = db.Column(db.String(50), nullable=False)
    target_id = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def log_action(user_id, action, target_table, target_id, description):
        log = AuditLog(
            user_id=user_id,
            action=action,
            target_table=target_table,
            target_id=target_id,
            description=description
        )
        db.session.add(log)
        db.session.commit()

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "target_table": self.target_table,
            "target_id": self.target_id,
            "description": self.description,
            "timestamp": self.timestamp.isoformat()
        }
