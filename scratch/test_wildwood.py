import urllib.request, ssl, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://www.wildwood-fl.gov/human-resources/pages/job-opportunities"
headers = {'User-Agent': 'Mozilla/5.0'}
try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
        html = r.read().decode('utf-8', errors='ignore')
        print("Status:", r.status, "Length:", len(html))
        # Look for job links or positions
        links = re.findall(r'href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html)
        for l, text in links:
            t = text.strip()
            if any(k in t.lower() for k in ['officer', 'technician', 'specialist', 'manager', 'coordinator', 'driver', 'utility', 'clerk', 'operator', 'supervisor']):
                print("Wildwood Job:", t, "->", l)
except Exception as e:
    print("Error:", e)
