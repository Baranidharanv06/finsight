#!/usr/bin/env python3
"""
VaultSight smoke test.
  python smoke_test.py http://localhost:8000
  python smoke_test.py http://<EC2-IP>:8000 --ingest --compare
Prints PASS/FAIL per check. Needs: pip install httpx boto3
"""
import argparse
import os
import sys

import httpx

REGION = "us-east-1"
CLIENT_ID = os.getenv("COGNITO_CLIENT_ID", "5vt84f5poh0hqkuqcblvkn45ai")
PASSWORD = os.getenv("TEST_PASSWORD", "Test@12345")
LEVEL = {"GUEST": 0, "EMPLOYEE": 1, "MANAGER": 2, "EXECUTIVE": 3}
QUESTION = "any pending litigation or regulatory issues?"

results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS  " if ok else "FAIL  ") + name + (f"  -> {detail}" if detail and not ok else ""))
    return bool(ok)


def get_token(group):
    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config
    c = boto3.client("cognito-idp", region_name=REGION, config=Config(signature_version=UNSIGNED))
    r = c.initiate_auth(
        AuthFlow="USER_PASSWORD_AUTH",
        ClientId=CLIENT_ID,
        AuthParameters={"USERNAME": f"{group.lower()}@test.com", "PASSWORD": PASSWORD},
    )
    return r["AuthenticationResult"]["AccessToken"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base_url")
    ap.add_argument("--ticker", default="AAPL")
    ap.add_argument("--ingest", action="store_true", help="also run a real manager ingest (slow)")
    ap.add_argument("--compare", action="store_true", help="also test /compare")
    a = ap.parse_args()
    base = a.base_url.rstrip("/")
    h = httpx.Client(timeout=180)

    def post(path, token=None, body=None):
        hd = {"Authorization": f"Bearer {token}"} if token else {}
        return h.post(base + path, json=body, headers=hd)

    print(f"\nTesting {base}\n")

    # 1. server up
    try:
        r = h.get(base + "/health")
        if not check("server answers /health", r.status_code == 200, f"status {r.status_code}"):
            return finish()
    except Exception as e:
        check("server answers /health", False, str(e)[:150])
        return finish()

    # 2. real Cognito tokens
    tokens = {}
    for g in LEVEL:
        try:
            tokens[g] = get_token(g)
            check(f"Cognito login as {g.lower()}@test.com", True)
        except Exception as e:
            check(f"Cognito login as {g.lower()}@test.com", False, str(e)[:150])
    if len(tokens) < 4:
        return finish()

    # 3. auth is enforced
    body = {"query": QUESTION, "ticker": a.ticker}
    check("/query without a token is rejected (401)", post("/query", None, body).status_code == 401)
    check("/ingest without a token is rejected (401)", post("/ingest", None, {"ticker": a.ticker}).status_code == 401)

    # 4. /query per clearance
    fulls = {}
    for g, lvl in LEVEL.items():
        r = post("/query", tokens[g], body)
        if not check(f"/query as {g} returns 200", r.status_code == 200, f"status {r.status_code} {r.text[:120]}"):
            continue
        d = r.json()
        if "disclosure_log" not in d:
            check(f"/query as {g}: data loaded for {a.ticker}", False,
                  "no disclosure_log (is the filing ingested on this server? run with --ingest)")
            continue
        log, src = d["disclosure_log"], d.get("sources", [])
        check(f"{g}: clearance comes from the token", d.get("clearance") == g, f"got {d.get('clearance')}")
        check(f"{g}: audit record written (request_id present)", bool(d.get("request_id")))
        check(f"{g}: sources line up with disclosure_log", len(src) == len(log), f"{len(src)} vs {len(log)}")
        bad_full = [x for x in log if x["decision"] == "FULL" and x["sensitivity"] > lvl]
        bad_deny = [x for x in log if x["sensitivity"] <= lvl and x["decision"] != "FULL"]
        check(f"{g}: never gets FULL text above its clearance", not bad_full, f"{len(bad_full)} chunk(s)")
        check(f"{g}: always gets FULL text it is cleared for", not bad_deny, f"{len(bad_deny)} chunk(s)")
        leaks = [i for i, x in enumerate(log)
                 if x["decision"] != "FULL" and i < len(src) and not str(src[i]).startswith("[")]
        check(f"{g}: withheld chunks carry no real text", not leaks, f"chunks {leaks}")
        fulls[g] = sum(1 for x in log if x["decision"] == "FULL")
    if len(fulls) == 4:
        order = [fulls[g] for g in ["GUEST", "EMPLOYEE", "MANAGER", "EXECUTIVE"]]
        check("more clearance never means less access", order == sorted(order), f"FULL counts {order}")

    # 5. ingest is locked down
    check("/ingest as EMPLOYEE is forbidden (403)",
          post("/ingest", tokens["EMPLOYEE"], {"ticker": a.ticker}).status_code == 403)
    check("/ingest as GUEST is forbidden (403)",
          post("/ingest", tokens["GUEST"], {"ticker": a.ticker}).status_code == 403)
    if a.ingest:
        r = post("/ingest", tokens["MANAGER"], {"ticker": a.ticker})
        ok = r.status_code == 200 and r.json().get("chunks_stored", 0) > 0
        check("/ingest as MANAGER works", ok, f"status {r.status_code} {r.text[:120]}")
        if ok:
            check("filing saved to S3 (s3_key present)", bool(r.json().get("s3_key")), "s3_key is null")

    # 6. compare
    if a.compare:
        r = post("/compare", tokens["EXECUTIVE"], {"query": QUESTION, "tickers": [a.ticker]})
        check("/compare as EXECUTIVE works", r.status_code == 200 and "answer" in r.json(), f"status {r.status_code}")

    finish()


def finish():
    p, t = sum(results), len(results)
    print(f"\n{p}/{t} checks passed" + ("  -- ALL GOOD" if p == t else f"  -- {t - p} FAILED"))
    sys.exit(0 if p == t else 1)


if __name__ == "__main__":
    main()
