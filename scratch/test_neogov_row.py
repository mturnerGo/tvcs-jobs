import urllib.request
import ssl
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'X-Requested-With': 'XMLHttpRequest'
}

url = "https://www.governmentjobs.com/careers/home/index?agency=wildwoodfl&sort=PositionTitle&isDescendingSort=false"
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
    html = resp.read().decode('utf-8', errors='ignore')
    soup = BeautifulSoup(html, 'html.parser')
    rows = soup.select('li.job-details-list-item, tr.job-table-row, div.job-item, li.list-item')
    print("Found rows:", len(rows))
    for r in rows[:3]:
        print("--- Row:", " | ".join(r.stripped_strings))
