# app/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(String, unique=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    farmer_input = Column(Text)
    crop = Column(String)
    region = Column(String)
    season = Column(String)
    ai_response = Column(Text)
    safe_label = Column(String)  # Safe / Moderate / Unsafe
    risk_level = Column(String)  # Low / Medium / High
    rule_triggered = Column(String)
    human_review_required = Column(Boolean, default=False)
    people_capacity = Column(String)      # Low/Medium/High
    infrastructure = Column(String)       # basic/limited/full
    organization_maturity = Column(String)
    human_review_required = Column(Boolean)
