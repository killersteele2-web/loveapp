from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

from .user import User
from .couple import Couple
from .couple_member import CoupleMember
from .memory import Memory
from .letter import Letter
from .timeline import TimelineEvent