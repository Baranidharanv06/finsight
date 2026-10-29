import urllib.request
import json

SERVER = "http://52.90.103.190:8000/query"
payload = json.dumps({"ticker": "AAPL", "query": "any pending litigation or regulatory issues?"}).encode("utf-8")

tokens = {
    "EXECUTIVE": input("Enter Executive JWT: ").strip(),
    "EMPLOYEE": input("Enter Employee JWT: ").strip(),
    "GUEST": input("Enter Guest JWT: ").strip()
}

for role, token in tokens.items():
    req = urllib.request.Request(
        SERVER,
        data=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode("utf-8"))
            print(f"\n--- Role: {role} ---")
            print(f"Clearance: {res.get('clearance')}")
            print(f"Disclosure Log Decisions: {[d['decision'] for d in res.get('disclosure_log', [])]}")
            print(f"Answer snippet: {res.get('answer', '')[:100]}...")
    except Exception as e:
        print(f"\n--- Role: {role} ---")
        print("Error:", e)
