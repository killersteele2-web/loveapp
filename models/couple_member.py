from datetime import datetime

from models import db


class CoupleMember(db.Model):
    __tablename__ = "couple_members"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    couple_id = db.Column(
        db.Integer,
        db.ForeignKey("couples.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    joined_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    couple = db.relationship(
        "Couple",
        back_populates="members"
    )

    user = db.relationship(
        "User",
        back_populates="couple_members"
    )
