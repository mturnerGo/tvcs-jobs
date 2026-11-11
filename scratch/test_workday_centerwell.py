import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://humana.wd5.myworkdayjobs.com/wday/cxs/humana/CenterWell_External_Career_Site/jobs"
payload = {
    "appliedFacets": {},
    "limit": 20,
    "offset": 0,
    "searchText": "Villages"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
try:
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print("Workday CXS Total:", data.get('total'))
        job_postings = data.get('jobPostings', [])
        for j in job_postings:
            print("Title:", j.get('title'))
            print("Location:", j.get('locationsText'))
            print("External Path:", j.get('externalPath'))
            print("Posted On:", j.get('postedOn'))
            print("---")
except Exception as e:
    print("Workday error:", e)
