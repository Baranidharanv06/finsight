import httpx

HEADERS = {"User-Agent": "FinSight yourname@email.com"}

cik = "0000320193"
r = httpx.get(f"https://data.sec.gov/submissions/CIK{cik}.json", headers=HEADERS).json()

filings = r["filings"]["recent"]
for i, form in enumerate(filings["form"]):
    if form == "10-K":
        print("Accession:", filings["accessionNumber"][i])
        print("Primary doc:", filings["primaryDocument"][i])
        print("Filing date:", filings["filingDate"][i])
        break