import urllib.request
import ssl
from bs4 import BeautifulSoup

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Accept': '*/*'
}

for agency in ['wildwoodfl', 'lsscedu', 'sumtercountyfl']:
    url = f"https://www.governmentjobs.com/careers/home/index?agency={agency}&sort=PositionTitle&isDescendingSort=false"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            links = soup.select('a.job-details-link')
            if not links:
                links = soup.select('a[href*="/jobs/"]')
            print(f"Agency '{agency}' => Found {len(links)} job links:")
            seen = set()
            for a in links:
                t = a.text.strip()
                h = a.get('href')
                if t and h and h not in seen:
                    seen.add(h)
                    print(f"  * {t} -> {h}")
    except Exception as e:
        print(f"Agency '{agency}' error: {e}")
