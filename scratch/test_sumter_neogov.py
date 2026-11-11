import urllib.request
import ssl
import json
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://www.governmentjobs.com/careers/sumtercountyfl"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
        html = r.read().decode('utf-8', errors='ignore')
        print("Status:", r.status)
        print("Length:", len(html))
        # Look for job postings or API
        jobs = re.findall(r'data-job-id="([^"]+)"[^>]*>.*?<a[^>]*class="job-details-link"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', html, re.DOTALL)
        print("Jobs found:", len(jobs))
        for j in jobs[:10]:
            print(j[2].strip(), "|", j[1])
        
        # Look for script tag with initial state or json
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
        for s in scripts:
            if 'jobPostings' in s or 'jobId' in s:
                print("Script snippet:", s[:300])
except Exception as e:
    print("Error:", e)
