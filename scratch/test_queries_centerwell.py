import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://humana.wd5.myworkdayjobs.com/wday/cxs/humana/CenterWell_External_Career_Site/jobs"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

for query in ["Lady Lake", "Wildwood", "32162", "32163"]:
    payload = {
        "appliedFacets": {},
        "limit": 20,
        "offset": 0,
        "searchText": query
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print(f"Query '{query}' => Total {data.get('total', 0)}")
            for j in data.get('jobPostings', [])[:3]:
                print("  *", j.get('title'), "|", j.get('locationsText'))
    except Exception as e:
        print(f"Error query {query}: {e}")
