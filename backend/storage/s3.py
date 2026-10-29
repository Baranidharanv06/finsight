import os
from datetime import datetime, timezone

FILINGS_BUCKET = os.getenv("FILINGS_BUCKET", "")
FILINGS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

_client = None


def _get_client():
    global _client
    if _client is None:
        import boto3
        _client = boto3.client("s3", region_name=FILINGS_REGION)
    return _client


def save_filing(ticker: str, text: str, doc_type: str = "10-K"):
    """Save the raw filing to S3 as filings/<TICKER>/<date>-<doc_type>.txt.
    Returns the S3 key, or None if the bucket is not configured or the write failed."""
    if not FILINGS_BUCKET:
        return None

    key = f"filings/{ticker}/{datetime.now(timezone.utc):%Y-%m-%d}-{doc_type}.txt"
    try:
        _get_client().put_object(
            Bucket=FILINGS_BUCKET,
            Key=key,
            Body=text.encode("utf-8"),
            ServerSideEncryption="AES256",
            ContentType="text/plain; charset=utf-8",
            Metadata={"ticker": ticker, "doc_type": doc_type},
        )
        return key
    except Exception as e:
        print(f"[storage] WARNING: could not save filing to S3: {e}")
        return None
