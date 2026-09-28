import os

from dotenv import load_dotenv


load_dotenv()


class Config:

    DATABASE_URL = os.getenv("DATABASE_URL")

    if DATABASE_URL:

        SQLALCHEMY_DATABASE_URI = DATABASE_URL

        SQLALCHEMY_ENGINE_OPTIONS = {
            "connect_args": {
                "ssl": {
                    "check_hostname": False
                }
            }
        }

    else:

        DB_HOST = os.getenv(
            "DB_HOST",
            "localhost"
        )

        DB_PORT = os.getenv(
            "DB_PORT",
            "3306"
        )

        DB_NAME = os.getenv(
            "DB_NAME",
            "love_app_db"
        )

        DB_USER = os.getenv(
            "DB_USER",
            "root"
        )

        DB_PASSWORD = os.getenv(
            "DB_PASSWORD",
            ""
        )

        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://"
            f"{DB_USER}:{DB_PASSWORD}"
            f"@{DB_HOST}:{DB_PORT}"
            f"/{DB_NAME}"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "development-secret-change-this"
    )

    JWT_ACCESS_TOKEN_EXPIRES = (
        60 * 60 * 24 * 7
    )