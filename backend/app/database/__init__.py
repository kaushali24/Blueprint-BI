from app.database.base import Base
from app.database.connection import SessionLocal, engine
from app.database.models import *


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
