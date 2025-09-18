import requests, json
from scoring import score_website

URL_TO_TEST = "https://mobilusdetailing.lt"
  # change this if you want another site

# Call your GitHub tool's /audit endpoint
resp = requests.post("http://127.0.0.1:8000/audit", json={"url": URL_TO_TEST}, timeout=180)
resp.raise_for_status()

# Extract audit data
audit = resp.json()
audit_data = audit.get("data", audit)  # handle {"data": {...}} or direct dict

# Run scoring
results = score_website(audit_data)

# Save raw audit data to a file
with open("audit_output.json", "w", encoding="utf-8") as f:
    json.dump(audit_data, f, indent=2, ensure_ascii=False)

# Save scores to a file
with open("score_output.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("✅ Files saved: audit_output.json and score_output.json")


