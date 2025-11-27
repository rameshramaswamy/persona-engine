import logging
import orjson
import time
from datetime import datetime

# Configure a specific logger for audit trails
audit_logger = logging.getLogger("audit_trail")
audit_logger.setLevel(logging.INFO)
handler = logging.FileHandler("audit_safety.jsonl") # Rotation needed in prod
audit_logger.addHandler(handler)

def log_safety_event(
    user_id: str, 
    input_text: str, 
    risk_scores: dict, 
    decision: str, 
    latency_ms: float
):
    """
    Writes a structured JSON log entry.
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "input_hash": hash(input_text), # Don't log full text if sensitive
        "scores": risk_scores,
        "decision": decision,
        "latency_ms": latency_ms
    }
    audit_logger.info(orjson.dumps(entry).decode('utf-8'))