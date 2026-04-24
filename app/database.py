from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# Use a more reliable database path for deployment
database_url = os.getenv("DATABASE_URL", "sqlite:///./cholo.db")
if database_url.startswith("sqlite"):
    SQLALCHEMY_DATABASE_URL = database_url.replace("sqlite://", "sqlite:///./")
else:
    SQLALCHEMY_DATABASE_URL = database_url

print(f"Database URL: {SQLALCHEMY_DATABASE_URL}")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")
