from datetime import datetime

from models import db


class Letter(db.Model):
    __tablename__ = "letters"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    couple_id = db.Column(
        db.Integer,
        db.ForeignKey("couples.id"),
        nullable=False
    )

    couple = db.relationship(
    "Couple",
    back_populates="letters"
    )

    title = db.Column(
        db.String(150),
        nullable=False
    )

    content = db.Column(
        db.Text,
        nullable=False
    )

    is_locked = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
