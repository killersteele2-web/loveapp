from datetime import datetime
import secrets
import string

from models import db


class Couple(db.Model):
    __tablename__ = "couples"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    invite_code = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    relationship_start_date = db.Column(
    db.Date,
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

    members = db.relationship(
        "CoupleMember",
        back_populates="couple",
        cascade="all, delete-orphan"
    )

    memories = db.relationship(
        "Memory",
        back_populates="couple"
    )

    letters = db.relationship(
        "Letter",
        back_populates="couple"
    )

    timeline_events = db.relationship(
        "TimelineEvent",
        back_populates="couple"
    )

    # ========================================================
    # INVITE CODE GENERATOR
    # ========================================================

    @staticmethod
    def generate_invite_code():
        characters = string.ascii_uppercase + string.digits

        while True:
            code = "LOVE-" + "".join(
                secrets.choice(characters)
                for _ in range(8)
            )

            existing = Couple.query.filter_by(
                invite_code=code
            ).first()

            if not existing:
                return code