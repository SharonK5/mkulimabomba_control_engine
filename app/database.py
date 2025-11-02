from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mkulimabomba.db")

Base = declarative_base()

class FarmProfile(Base):
    __tablename__ = "farm_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    location = Column(String)
    crop_type = Column(String)
    farm_size = Column(String)
    soil_type = Column(String)
    experience_level = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class QueryLog(Base):
    __tablename__ = "query_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    query = Column(Text)
    farm_profile = Column(JSON)
    policy_decisions = Column(JSON)
    ai_response = Column(Text)
    audit_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, index=True)
    name = Column(String)
    region = Column(String)
    user_type = Column(String)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
