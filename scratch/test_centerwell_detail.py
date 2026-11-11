import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://humana.wd5.myworkdayjobs.com/wday/cxs/humana/CenterWell_External_Career_Site/jobs"
payload = {
    "appliedFacets": {},
    "limit": 5,
    "offset": 0,
    "searchText": "Villages"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
    data = json.loads(resp.read().decode('utf-8'))
    first_job = data.get('jobPostings', [])[0]
    print("Keys in job item:", json.dumps(first_job, indent=2))
    
    # Also fetch detail of first job:
    path = first_job.get('externalPath')
    detail_url = f"https://humana.wd5.myworkdayjobs.com/wday/cxs/humana/CenterWell_External_Career_Site{path}"
    print(f"\nDetail URL: {detail_url}")
    req2 = urllib.request.Request(detail_url, headers=headers)
    with urllib.request.urlopen(req2, context=ctx, timeout=15) as resp2:
        detail = json.loads(resp2.read().decode('utf-8'))
        job_info = detail.get('jobPostingInfo', {})
        print("Detail Keys:", list(job_info.keys()))
        print("Time type:", job_info.get('timeType'))
        print("Job Req Id:", job_info.get('jobReqId'))
        print("Location:", job_info.get('location'))
        print("Address:", job_info.get('additionalLocations'))
        print("External URL:", job_info.get('externalUrl'))
