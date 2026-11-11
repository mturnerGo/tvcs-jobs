import urllib.request, ssl, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = 'https://agency.governmentjobs.com/sumtercountyfl/default.cfm'
r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), context=ctx, timeout=10)
html = r.read().decode('utf-8', errors='ignore')

# search for "job" or "table" or "grid"
print("Contains 'job-details':", 'job-details' in html)
print("Contains 'jobId':", 'jobId' in html)
print("Contains 'jobTable':", 'jobTable' in html)

for line in html.splitlines():
    if 'job' in line.lower() and ('href' in line or 'class' in line or 'id' in line):
        print(line[:120].strip())
        if 'title' in line.lower() or 'href' in line.lower():
            break
