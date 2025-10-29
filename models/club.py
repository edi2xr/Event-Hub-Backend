from extensions import db

class Club(db.Model):
    __tablename__ = "clubs"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)

    members = db.relationship("User", back_populates="club", cascade="all, delete")
    events = db.relationship("Event", back_populates="club", cascade="all, delete")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description
        }
