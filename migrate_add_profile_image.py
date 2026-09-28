from app import app
from models import db


with app.app_context():

    print("Adding profile_image column...")

    db.session.execute(
        db.text(
            """
            ALTER TABLE users
            ADD COLUMN profile_image VARCHAR(255) NULL
            """
        )
    )

    db.session.commit()

    print("profile_image column added successfully.")