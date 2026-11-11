import urllib.request
import json
import ssl
from concurrent.futures import ThreadPoolExecutor

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def fetch_detail(path):
    url = f"https://humana.wd5.myworkdayjobs.com/wday/cxs/humana/CenterWell_External_Career_Site{path}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            info = data.get('jobPostingInfo', {})
            return {
                "timeType": info.get('timeType', 'Full time'),
                "applyUrl": info.get('externalUrl') or f"https://humana.wd5.myworkdayjobs.com/CenterWell_External_Career_Site{path}",
                "jobReqId": info.get('jobReqId', ''),
                "postedDate": info.get('startDate', ''),
                "location": info.get('location', '')
            }
    except Exception as e:
        return {"timeType": "Full time", "applyUrl": f"https://humana.wd5.myworkdayjobs.com/CenterWell_External_Career_Site{path}"}

paths = [
    "/job/The-Villages-FL/Medical-Coding-Coordinator-1_R-428907-1",
    "/job/Lady-Lake-FL/Medical-Coding-Coordinator---Villages--Spanish-Springs-_R-432928",
    "/job/The-Villages-FL/Home-Health-Speech-Language-Pathologist-Per-Diem_R-416174"
]

with ThreadPoolExecutor(max_workers=5) as ex:
    results = list(ex.map(fetch_detail, paths))
for r in results:
    print(r)
