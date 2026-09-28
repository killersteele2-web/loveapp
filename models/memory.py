from datetime import datetime

from models import db


class Memory(db.Model):
    __tablename__ = "memories"

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
    back_populates="memories"
    )

    title = db.Column(
        db.String(150),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    image_path = db.Column(
        db.String(500),
        nullable=True
    )

    memory_date = db.Column(
        db.Date,
        nullable=True
    )

    is_favorite = db.Column(
        db.Boolean,
        nullable=False,
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
