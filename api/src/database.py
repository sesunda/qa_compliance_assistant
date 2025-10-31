from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator
from api.src.config import settings

# Create the engine and a session factory. Annotate SessionLocal to help type checkers.
engine = create_engine(settings.DATABASE_URL)
# SQLAlchemy 2.0 supports parameterizing sessionmaker with Session for typing
SessionLocal: sessionmaker[Session] = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # type: ignore[assignment]

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency that yields a DB session and ensures it is closed.

    Use in FastAPI routes as: db: Session = Depends(get_db)
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
