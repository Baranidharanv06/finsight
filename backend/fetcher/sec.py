import httpx
import re
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "FinSight yourname@email.com"}

def get_cik(ticker: str) -> str:
    r = httpx.get("https://www.sec.gov/files/company_tickers.json", headers=HEADERS)
    for entry in r.json().values():
        if entry["ticker"].upper() == ticker.upper():
            return str(entry["cik_str"]).zfill(10)
    raise ValueError(f"Ticker '{ticker}' not found")

def get_latest_10k_text(cik: str) -> str:
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    r = httpx.get(url, headers=HEADERS).json()

    filings = r["filings"]["recent"]
    for i, form in enumerate(filings["form"]):
        if form == "10-K":
            accession = filings["accessionNumber"][i].replace("-", "")
            primary_doc = filings["primaryDocument"][i]

            filing_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/{primary_doc}"
            raw_html = httpx.get(filing_url, headers=HEADERS, timeout=180.0).text
            return _extract_text(raw_html)

    raise ValueError("No 10-K document found")

def _extract_text(raw_html: str) -> str:
    soup = BeautifulSoup(raw_html, "html.parser")

    for tag in soup.find_all(["script", "style", "table"]):
        tag.decompose()

    # Remove entire hidden XBRL data sections
    for tag in soup.find_all(re.compile(r"^ix:(header|resources|nonnumeric|nonfraction)", re.I)):
        tag.decompose()

    # Remove anything hidden via style
    for tag in soup.find_all(style=re.compile(r"display:\s*none")):
        tag.decompose()

    text = soup.get_text(separator="\n")
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[A-Za-z0-9]+:[A-Za-z][A-Za-z0-9]*", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()