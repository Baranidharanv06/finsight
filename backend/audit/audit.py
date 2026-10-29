import json
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal

AUDIT_ENABLED = os.getenv("AUDIT_ENABLED", "true").lower() == "true"
AUDIT_TABLE = os.getenv("AUDIT_TABLE", "vaultsight-audit")
AUDIT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

_table = None


def _get_table():
    global _table
    if _table is None:
        import boto3
        _table = boto3.resource("dynamodb", region_name=AUDIT_REGION).Table(AUDIT_TABLE)
    return _table


def log_disclosure(user_id: str, clearance: str, ticker: str, query: str, decisions: list[dict]):
    """Write one audit record. Returns the request_id, or None if not written."""
    if not AUDIT_ENABLED:
        return None

    request_id = str(uuid.uuid4())
    item = {
        "request_id": request_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "clearance": clearance,
        "ticker": ticker,
        "query": query[:500],
        "decisions": decisions,
    }
    try:
        _get_table().put_item(Item=json.loads(json.dumps(item), parse_float=Decimal))
        return request_id
    except Exception as e:
        print(f"[audit] WARNING: could not write audit record {request_id}: {e}")
        return None
