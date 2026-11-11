import urllib.request
import re
import json

url = 'https://www.centerwellcareers.com/us/en/search-results?keywords=The%20Villages'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

try:
    with urllib.request.urlopen(req, timeout=15) as r:
        html = r.read().decode('utf-8', errors='ignore')
        print("Length:", len(html))
        # Check for phApp or phenom config
        ph = re.findall(r'phApp\.ddo\s*=\s*(\{.*?\});', html, re.DOTALL)
        if ph:
            print("Found phApp.ddo!")
            ddo = json.loads(ph[0])
            print("Keys:", ddo.keys())
            refData = ddo.get('eagerLoadRefineSearch', {})
            jobs = refData.get('data', {}).get('jobs', [])
            total = refData.get('data', {}).get('totalHits', 0)
            print(f"Total jobs for 'The Villages': {total}")
            for j in jobs[:5]:
                print("-", j.get('title'), "|", j.get('city'), j.get('state'), "|", j.get('applyUrl'))
        else:
            print("No phApp.ddo, searching for API endpoints...")
            matches = re.findall(r'/api/[^"\']+', html)
            print("API matches:", set(matches[:10]))
except Exception as e:
    print("Error:", e)
