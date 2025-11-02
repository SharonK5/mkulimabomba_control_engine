# app/audit_logger.py
import json
import uuid
from datetime import datetime
import hashlib
from pathlib import Path

AUDIT_LOG_PATH = Path("logs/audit_trail.jsonl")  # JSONL for streaming
AUDIT_LOG_PATH.parent.mkdir(exist_ok=True)

def generate_audit_id() -> str:
    return f"AUDIT-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"

def log_full_audit(
    farmer_input: str,
    farm_context: dict,  # includes crop, region, season, etc.
    ai_response: dict,
    safety_label: str,  # "Safe", "Moderate", "Unsafe"
    rule_triggered: str,
    risk_level: str,
    adaptation_notes: str = "",
    learning_feedback: str = "",
    requires_human_review: bool = False
):
    audit_id = generate_audit_id()
    
    record = {
        "Audit ID": audit_id,
        "Timestamp": datetime.utcnow().isoformat() + "Z",
        "Farmer Input": farmer_input,
        **farm_context,  # unpacks Crop, Region, Season, etc.
        "AI Response": ai_response.get("text", str(ai_response)),
        "Safe / Moderate / Unsafe": safety_label,
        "Rule Triggered": rule_triggered,
        "Risk Level": risk_level,
        "Adaptation Notes": adaptation_notes,
        "Learning / Feedback": learning_feedback,
        "Human in the Loop Required": requires_human_review,
        "Blockchain Placeholder": ""  # populated later if needed
    }

    # Optional: generate immutable hash
    record_hash = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
    record["Blockchain Placeholder"] = record_hash[:16]  # short hash for demo

    # Append as JSONL (one JSON per line)
    with open(AUDIT_LOG_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")

    return audit_id
