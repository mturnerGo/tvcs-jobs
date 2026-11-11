import urllib.request
import json
import ssl
from concurrent.futures import ThreadPoolExecutor

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def harvest_tvh_centerwell():
    print("Harvesting The Villages Health / CenterWell Senior Primary Care...")
    jobs = []
    base_url = "https://humana.wd5.myworkdayjobs.com/wday/cxs/humana/CenterWell_External_Career_Site"
    jobs_url = f"{base_url}/jobs"
    
    headers = dict(HEADERS)
    headers['Content-Type'] = 'application/json'
    headers['Accept'] = 'application/json'
    
    queries = ["Villages", "Lady Lake"]
    seen_paths = set()
    
    for query in queries:
        offset = 0
        limit = 20
        while True:
            payload = json.dumps({
                "appliedFacets": {},
                "limit": limit,
                "offset": offset,
                "searchText": query
            }).encode('utf-8')
            try:
                req = urllib.request.Request(jobs_url, data=payload, headers=headers)
                with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    postings = data.get('jobPostings', [])
                    total = data.get('total', 0)
                    if not postings:
                        break
                    
                    for p in postings:
                        path = p.get('externalPath', '')
                        if not path or path in seen_paths:
                            continue
                        seen_paths.add(path)
                        
                        title = p.get('title', '').strip()
                        loc_text = p.get('locationsText', 'The Villages, FL')
                        
                        # Filter to only relevant locations
                        loc_lower = loc_text.lower()
                        t_lower = title.lower()
                        if not ('village' in loc_lower or 'lady lake' in loc_lower or 'village' in t_lower):
                            continue
                            
                        # Determine Full-Time vs Part-Time/PRN
                        full_time = True
                        if any(k in t_lower for k in ['per diem', 'prn', 'part time', 'part-time', 'temporary', 'pool']):
                            full_time = False
                            
                        posted_on = p.get('postedOn', 'Recent')
                        apply_url = f"https://humana.wd5.myworkdayjobs.com/CenterWell_External_Career_Site{path}"
                        
                        # Format plaza / care center location
                        plaza = "The Villages Care Centers"
                        for pz in ["Powell Rd", "Spanish Springs", "Santa Barbara", "Colony", "Pinellas", "Mulberry Grove", "Brownwood"]:
                            if pz.lower() in t_lower:
                                plaza = f"The Villages Health - {pz} Care Center"
                                break
                                
                        jobs.append({
                            "Job_Title": f"The Villages Health - {title}",
                            "Company": "The Villages Health / CenterWell",
                            "Category": "CATEGORY III",
                            "Priority_Tier": 3,
                            "Priority_Label": "Category III (Commercial Tenant - 3rd Priority)",
                            "Employment_Type": "Full-Time" if full_time else "Part-Time",
                            "TVCS_Qualifying": full_time,
                            "Plaza_Location": plaza,
                            "Location": loc_text,
                            "Phone": "(352) 674-1710",
                            "Estimated_Salary": "Competitive Healthcare & Clinical Scale",
                            "Source": "The Villages Health (Official CenterWell Workday ATS)",
                            "Job_Link": apply_url,
                            "Posted_Date": posted_on,
                            "Description": f"Primary and specialty care position with The Villages Health at {plaza}. {'Full-time continuous employment qualifies for Category III TVCS enrollment priority.' if full_time else 'Part-time / PRN healthcare position.'}"
                        })
                    
                    offset += len(postings)
                    if offset >= total:
                        break
            except Exception as e:
                print(f"Error fetching CenterWell query '{query}': {e}")
                break
                
    print(f"Captured {len(jobs)} jobs from The Villages Health / CenterWell.")
    return jobs

res = harvest_tvh_centerwell()
for j in res[:5]:
    print(j['Job_Title'], "->", j['Plaza_Location'], "|", j['Employment_Type'])
