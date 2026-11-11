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

all_postings = []
offset = 0
limit = 20

while True:
    payload = {
        "appliedFacets": {},
        "limit": limit,
        "offset": offset,
        "searchText": "Villages"
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        total = data.get('total', 0)
        postings = data.get('jobPostings', [])
        if not postings:
            break
        all_postings.extend(postings)
        offset += len(postings)
        if offset >= total:
            break

print(f"Total CenterWell / TVH jobs captured: {len(all_postings)}")
for p in all_postings:
    print(f"- {p.get('title')} | {p.get('locationsText')} | {p.get('postedOn')}")
