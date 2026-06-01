from backend.fetcher.sec import get_cik, get_latest_10k_text

cik = get_cik("AAPL")
print("CIK:", cik)

text = get_latest_10k_text(cik)
print(text[:500])  # just first 500 chars