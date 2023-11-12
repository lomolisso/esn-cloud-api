from app.database import SessionLocal
from sqlalchemy.orm import Session


def get_session() -> Session:
    """
    Database dependency: allows a single Session per request.
    """   
    with SessionLocal() as session:
        yield session