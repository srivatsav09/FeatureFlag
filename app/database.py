from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings


# Create the database engine
# The engine manages connections to the database
engine = create_engine(
    settings.database_url,
    echo=settings.debug,  # Log SQL queries when debug=True
)

# Create a session factory
# Sessions are how we interact with the database (query, insert, update)
SessionLocal = sessionmaker(
    autocommit=False,  # We control when to commit transactions
    autoflush=False,   # We control when to flush changes
    bind=engine,       # Use our engine
)


# Base class for all our models
# Every database table model will inherit from this
class Base(DeclarativeBase):
    pass


def get_db():
    """
    Dependency that provides a database session.
    Used in FastAPI endpoints to get a database connection.
    Automatically closes the session when the request is done.
    """
    db = SessionLocal()
    try:
        yield db  # Provide the session to the endpoint
    finally:
        db.close()  # Always close when done
