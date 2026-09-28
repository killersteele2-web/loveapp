from flask import Flask
from sqlalchemy import text

from config import Config
from models import db


def migrate():

    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():

        connection = db.engine.connect()
        transaction = connection.begin()

        try:

            print("Starting LoveApp database migration...")

            # ==================================================
            # 1. Add couple_id as nullable
            # ==================================================

            print("Adding couple_id to memories...")

            connection.execute(
                text("""
                    ALTER TABLE memories
                    ADD COLUMN couple_id INT NULL
                """)
            )

            print("Adding couple_id to letters...")

            connection.execute(
                text("""
                    ALTER TABLE letters
                    ADD COLUMN couple_id INT NULL
                """)
            )

            print("Adding couple_id to timeline_events...")

            connection.execute(
                text("""
                    ALTER TABLE timeline_events
                    ADD COLUMN couple_id INT NULL
                """)
            )

            # ==================================================
            # 2. Create the initial couple
            # ==================================================

            print("Creating initial couple...")

            connection.execute(
                text("""
                    INSERT INTO couples (
                        invite_code
                    )
                    VALUES (
                        'LOVEAPP-LEGACY'
                    )
                """)
            )

            couple_id = connection.execute(
                text("""
                    SELECT id
                    FROM couples
                    WHERE invite_code = 'LOVEAPP-LEGACY'
                """)
            ).scalar()

            print(f"Initial couple created: {couple_id}")

            # ==================================================
            # 3. Assign existing data to the couple
            # ==================================================

            connection.execute(
                text("""
                    UPDATE memories
                    SET couple_id = :couple_id
                    WHERE couple_id IS NULL
                """),
                {
                    "couple_id": couple_id
                }
            )

            connection.execute(
                text("""
                    UPDATE letters
                    SET couple_id = :couple_id
                    WHERE couple_id IS NULL
                """),
                {
                    "couple_id": couple_id
                }
            )

            connection.execute(
                text("""
                    UPDATE timeline_events
                    SET couple_id = :couple_id
                    WHERE couple_id IS NULL
                """),
                {
                    "couple_id": couple_id
                }
            )

            # ==================================================
            # 4. Make couple_id required
            # ==================================================

            print("Making couple_id required...")

            connection.execute(
                text("""
                    ALTER TABLE memories
                    MODIFY COLUMN couple_id INT NOT NULL
                """)
            )

            connection.execute(
                text("""
                    ALTER TABLE letters
                    MODIFY COLUMN couple_id INT NOT NULL
                """)
            )

            connection.execute(
                text("""
                    ALTER TABLE timeline_events
                    MODIFY COLUMN couple_id INT NOT NULL
                """)
            )

            # ==================================================
            # 5. Add foreign keys
            # ==================================================

            print("Adding foreign keys...")

            connection.execute(
                text("""
                    ALTER TABLE memories
                    ADD CONSTRAINT fk_memories_couple
                    FOREIGN KEY (couple_id)
                    REFERENCES couples(id)
                    ON DELETE CASCADE
                """)
            )

            connection.execute(
                text("""
                    ALTER TABLE letters
                    ADD CONSTRAINT fk_letters_couple
                    FOREIGN KEY (couple_id)
                    REFERENCES couples(id)
                    ON DELETE CASCADE
                """)
            )

            connection.execute(
                text("""
                    ALTER TABLE timeline_events
                    ADD CONSTRAINT fk_timeline_events_couple
                    FOREIGN KEY (couple_id)
                    REFERENCES couples(id)
                    ON DELETE CASCADE
                """)
            )

            transaction.commit()

            print()
            print("======================================")
            print("Migration completed successfully!")
            print("======================================")
            print(f"Legacy couple ID: {couple_id}")
            print("Existing data has been preserved.")

        except Exception as error:

            transaction.rollback()

            print()
            print("======================================")
            print("Migration FAILED")
            print("======================================")
            print(error)

            raise

        finally:

            connection.close()


if __name__ == "__main__":
    migrate()
