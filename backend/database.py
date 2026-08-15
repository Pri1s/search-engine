import os

from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

Base = declarative_base()
engine = create_engine(os.getenv("DATABASE_URL"))
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# create & cleans up database sessions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

