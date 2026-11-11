import urllib.request
import ssl
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

gov_url = 'https://www.governmentjobs.com/careers/home/index?agency=sumtercountyfl&sort=PositionTitle&isDescendingSort=false'
headers = {'User-Agent': 'Mozilla/5.0'}
req = urllib.request.Request(gov_url, headers=headers)
r = urllib.request.urlopen(req, context=ctx, timeout=10)
soup = BeautifulSoup(r.read(), 'html.parser')
links = soup.select('a[href*="/careers/sumtercountyfl/jobs/"]')
print("Found links:", len(links))
for a in links:
    print(a.text.strip(), "->", a['href'])
