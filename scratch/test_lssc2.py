import urllib.request, ssl, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
url = 'https://www.lssc.edu/faculty-staff/human-resources/employment-opportunities/'
try:
    r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), context=ctx, timeout=10)
    html = r.read().decode('utf-8', errors='ignore')
    print('Len:', len(html))
    links = re.findall(r'href=["\'](https?://[^"\']+)["\']', html)
    for l in set(links):
        if any(k in l.lower() for k in ['job', 'career', 'workday', 'icims', 'peopleadmin', 'adp', 'interviewexchange', 'neo']):
            print('ATS:', l)
except Exception as e:
    print('Error:', e)
