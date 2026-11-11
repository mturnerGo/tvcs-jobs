import urllib.request, ssl, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
url = 'https://www.lssc.edu/dept/hr/work-with-us/'
try:
    r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), context=ctx, timeout=10)
    html = r.read().decode('utf-8', errors='ignore')
    print('Len:', len(html))
    links = set(re.findall(r'href=["\'](https?://[^"\']+)["\']', html))
    for l in links:
        print("Link:", l)
except Exception as e:
    print('Error:', e)
