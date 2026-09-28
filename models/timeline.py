from datetime import datetime

from models import db


class TimelineEvent(db.Model):
    __tablename__ = "timeline_events"

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
    back_populates="timeline_events"
    )

    title = db.Column(
        db.String(150),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    event_date = db.Column(
        db.Date,
        nullable=False
    )

    image_path = db.Column(
        db.String(500),
        nullable=True
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
