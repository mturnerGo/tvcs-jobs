import urllib.request
import ssl
import json
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

url = 'https://thevillageshealth.com/careers/'
print(f"Fetching {url}...")
try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
        html = r.read().decode('utf-8', errors='ignore')
        print("Length:", len(html))
        # Look for links
        links = set(re.findall(r'href=["\'](https?://[^"\']+)["\']', html))
        for l in links:
            if any(k in l.lower() for k in ['job', 'career', 'workday', 'icims', 'ultipro', 'adp', 'greenhouse', 'paylocity', 'humana', 'centerwell']):
                print("ATS/Career link:", l)
        
        # Look for iframes or embeds
        iframes = set(re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', html, re.I))
        for ifr in iframes:
            print("Iframe:", ifr)
except Exception as e:
    print("Error:", e)
