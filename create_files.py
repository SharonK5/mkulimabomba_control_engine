import os

# Create database.py
database_content = '''from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Text
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
'''

main_content = '''from fastapi import FastAPI

app = FastAPI(
    title="MkulimaBomba Control Engine",
    description="AI-powered agricultural decision support system",
    version="2.0.0"
)

@app.get("/")
async def root():
    return {"message": "MkulimaBomba Control Engine API - Healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "control_engine"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''

audit_logger_content = '''import json
import uuid
from datetime import datetime
from typing import Dict, Any

class AuditLogger:
    def __init__(self, log_file: str = "audit_logs.jsonl"):
        self.log_file = log_file
    
    def log_interaction(self, query: str, farm_profile: Dict[str, Any], 
                       policy_decisions: Dict[str, Any], ai_response: str, user_id: str = "anonymous") -> str:
        audit_id = str(uuid.uuid4())
        
        log_entry = {
            "audit_id": audit_id,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "query": query,
            "farm_profile": farm_profile,
            "policy_decisions": policy_decisions,
            "ai_response": ai_response
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\\n')
        
        return audit_id
'''

# Write the files
with open('app/database.py', 'w') as f:
    f.write(database_content)

with open('app/main.py', 'w') as f:
    f.write(main_content)

with open('app/audit_logger.py', 'w') as f:
    f.write(audit_logger_content)

print("Files created successfully!")
