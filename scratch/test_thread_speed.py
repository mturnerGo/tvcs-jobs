import urllib.request
import json
import ssl
from concurrent.futures import ThreadPoolExecutor

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def get_detail(path):
    url = f"https://humana.wd5.myworkdayjobs.com/wday/cxs/humana/CenterWell_External_Career_Site{path}"
    headers = dict(HEADERS)
    headers['Content-Type'] = 'application/json'
    headers['Accept'] = 'application/json'
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
            info = json.loads(r.read().decode('utf-8')).get('jobPostingInfo', {})
            return path, info.get('timeType', 'Full time'), info.get('jobReqId', ''), info.get('startDate', '')
    except Exception:
        return path, 'Full time', '', ''

paths = ["/job/The-Villages-FL/Medical-Coding-Coordinator-1_R-428907-1", "/job/The-Villages-FL/Home-Health-Speech-Language-Pathologist-Per-Diem_R-416174"]
with ThreadPoolExecutor(max_workers=4) as ex:
    results = dict(ex.map(lambda p: (p[0], p[1:]), ex.map(get_detail, paths)))
print(results)
