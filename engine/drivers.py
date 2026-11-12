"""
Universal ATS Protocol Drivers
------------------------------
Standardized API fetchers for common applicant tracking systems:
- iCIMS / Jibe REST API
- Workday CXS JSON API
- ADP Workforce Now Public API
- NEOGOV GovernmentJobs API
- ClearCompany REST API
- UltiPro / UKG Pro Public Board
- Workstream ATS API
- Dayforce HCM Headless Scraper
"""

import urllib.request
import urllib.parse
import ssl
import json
import re
from bs4 import BeautifulSoup

SSL_CTX = ssl._create_unverified_context()
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*'
}

def fetch_json(url, data=None, headers=None, timeout=12):
    hdrs = DEFAULT_HEADERS.copy()
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, data=data, headers=hdrs)
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8', errors='ignore'))

# 1. iCIMS / Jibe Driver (e.g. UF Health)
def driver_icims_jibe(feed):
    jobs = []
    base_url = feed['url']
    params = feed.get('params', {'location': 'The Villages', 'limit': 100})
    company = feed['company']

    for page in range(1, 5):
        query_params = params.copy()
        query_params['page'] = page
        qs = urllib.parse.urlencode(query_params)
        full_url = f"{base_url}?{qs}"
        try:
            data = fetch_json(full_url)
            results = data.get('jobs', [])
            if not results:
                break
            for item in results:
                d = item.get('data', {})
                title = d.get('title')
                if not title:
                    continue
                apply_url = d.get('apply_url') or d.get('url') or base_url
                city = d.get('city', 'The Villages')
                state = d.get('state', 'FL')
                loc_str = f"{city}, {state}" if city else "The Villages, FL"
                emp_type = d.get('employment_type', 'Full-Time')

                jobs.append({
                    "Job_Title": title.strip(),
                    "Company": company,
                    "Estimated_Salary": "Competitive / Direct Benefits",
                    "Location": loc_str,
                    "Job_Link": apply_url,
                    "Description": f"Active verified healthcare requisition with {company}.",
                    "Employment_Type": emp_type
                })
            total = data.get('totalCount', 0)
            if len(jobs) >= total or len(results) < params.get('limit', 100):
                break
        except Exception as e:
            print(f"[iCIMS] Error fetching page {page} for {company}: {e}")
            break
    return jobs

# 2. Workday CXS Driver (e.g. CenterWell / The Villages Health)
def driver_workday_cxs(feed):
    jobs = []
    base_url = feed.get('base_url')
    if not base_url:
        tenant = feed['tenant']
        site = feed['site']
        base_url = f"https://{tenant}.wd1.myworkdayjobs.com/wday/cxs/{tenant}/{site}"
    
    jobs_url = f"{base_url}/jobs"
    queries = feed.get('search_queries', [feed.get('search_text', 'The Villages')])
    company = feed['company']
    seen_paths = set()

    for q in queries:
        offset = 0
        limit = 20
        while True:
            payload = json.dumps({
                "appliedFacets": {},
                "limit": limit,
                "offset": offset,
                "searchText": q
            }).encode('utf-8')
            try:
                data = fetch_json(jobs_url, data=payload, headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                })
                postings = data.get('jobPostings', [])
                if not postings:
                    break
                for p in postings:
                    ext = p.get('externalPath', '')
                    title = p.get('title', '')
                    if not title or not ext or ext in seen_paths:
                        continue
                    seen_paths.add(ext)
                    loc = p.get('locationsText', 'The Villages, FL')
                    loc_lower = loc.lower()
                    if 'bangalore' in loc_lower or 'india' in loc_lower:
                        continue
                    filter_kws = feed.get('filter_keywords')
                    if filter_kws and not any(k in loc_lower for k in filter_kws):
                        continue
                    clean_base = base_url.replace('/wday/cxs', '')
                    job_url = f"{clean_base}{ext}"

                    jobs.append({
                        "Job_Title": title.strip(),
                        "Company": company,
                        "Estimated_Salary": "Competitive / Full Benefits",
                        "Location": loc,
                        "Job_Link": job_url,
                        "Description": f"Verified position with {company}.",
                        "Employment_Type": "Full-Time"
                    })
                total = data.get('total', 0)
                offset += limit
                if offset >= total or len(postings) < limit:
                    break
            except Exception as e:
                print(f"[Workday] Error for {company} (query: {q}): {e}")
                break
    return jobs

# 3. ADP Workforce Now Driver (e.g. TVCS, The Villages, VCCDD)
def driver_adp_wfn(feed):
    jobs = []
    cid = feed['cid']
    company = feed['company']
    api_url = f"https://workforcenow.adp.com/mascsr/default/careercenter/public/events/staffing/v1/job-requisitions?cid={cid}&timeStamp=1000"

    try:
        data = fetch_json(api_url)
        reqs = data.get('jobRequisitions', [])
        for r in reqs:
            title = r.get('requisitionTitle', '').strip()
            item_id = r.get('itemID', '')
            if not title or not item_id:
                continue
            apply_link = f"https://workforcenow.adp.com/mascsr/default/mdf/recruitment/recruitment.html?cid={cid}&jobId={item_id}"
            
            jobs.append({
                "Job_Title": title,
                "Company": company,
                "Estimated_Salary": "Competitive / Direct Operating Benefits",
                "Location": "The Villages, FL",
                "Job_Link": apply_link,
                "Description": f"Active verified opening with {company}.",
                "Employment_Type": "Full-Time"
            })
    except Exception as e:
        print(f"[ADP] Error for {company}: {e}")
    return jobs

# 4. NEOGOV Driver (e.g. City of Wildwood, Lake-Sumter State College, Sumter County)
def driver_neogov(feed):
    jobs = []
    agency_id = feed['agency']
    company = feed['company']
    url = f"https://www.governmentjobs.com/careers/home/index?agency={agency_id}&sort=PositionTitle&isDescendingSort=false"
    
    gov_headers = DEFAULT_HEADERS.copy()
    gov_headers['X-Requested-With'] = 'XMLHttpRequest'

    try:
        req = urllib.request.Request(url, headers=gov_headers)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=12) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(content, 'html.parser')
            rows = soup.select('li.list-item, tr.job-table-row, li.job-details-list-item')
            seen_links = set()
            
            for r in rows:
                link_el = r.select_one('a.item-details-link, a.job-details-link, a[href*="/jobs/"]')
                if not link_el:
                    continue
                title = link_el.get_text(strip=True)
                href = link_el.get('href', '')
                if not href.startswith('http'):
                    href = f"https://www.governmentjobs.com{href}"
                if href in seen_links or not title:
                    continue
                seen_links.add(href)
                salary_el = r.select_one('.job-item-salary, .salary, span[class*="salary"]')
                salary = salary_el.get_text(strip=True) if salary_el else "Competitive / Public Retirement"

                jobs.append({
                    "Job_Title": title,
                    "Company": company,
                    "Estimated_Salary": salary,
                    "Location": "The Villages / Sumter County, FL",
                    "Job_Link": href,
                    "Description": f"Public sector position with {company}.",
                    "Employment_Type": "Full-Time"
                })
    except Exception as e:
        print(f"[NEOGOV] Error for {company}: {e}")
    return jobs

# 5. ClearCompany Driver (e.g. FMK Hospitality Group)
def driver_clearcompany_api(feed):
    jobs = []
    api_uuid = feed['api_uuid']
    apply_base = feed.get('apply_base', 'https://fmkhospitalitygroup.clearcompany.com/careers/jobs')
    company = feed['company']
    api_url = f"https://careers-api.clearcompany.com/v1/{api_uuid}?pageIndex=0&pageSize=100"

    try:
        data = fetch_json(api_url)
        results = data.get('results', [])
        for j in results:
            title = j.get('positionTitle')
            jid = j.get('id')
            if not title or not jid:
                continue
            city = j.get('city')
            state = j.get('state') or 'FL'
            loc_str = f"{city}, {state}" if city else "The Villages, FL"
            apply_url = f"{apply_base}/{jid}/apply"

            jobs.append({
                "Job_Title": title.strip(),
                "Company": company,
                "Estimated_Salary": "$15 - $26/hr or Commensurate with Experience",
                "Location": loc_str,
                "Job_Link": apply_url,
                "Description": f"Active verified opening with {company}. Hospitality & dining partner in The Villages town squares and country clubs.",
                "Employment_Type": "Full-Time"
            })
    except Exception as e:
        print(f"[ClearCompany] Error for {company}: {e}")
    return jobs

# 6. UltiPro / UKG Pro Board Driver (e.g. Seacoast National Bank)
def driver_ultipro_board(feed):
    jobs = []
    tenant = feed['tenant']
    board = feed['board']
    company = feed['company']
    api_url = f"https://recruiting.ultipro.com/{tenant}/JobBoard/{board}/JobBoardView/LoadSearchResults"
    payload = json.dumps({"opportunitySearch": {"Top": 100, "Skip": 0, "QueryWord": "The Villages"}}).encode('utf-8')

    try:
        data = fetch_json(api_url, data=payload, headers={'Content-Type': 'application/json'})
        opps = data.get('opportunities', [])
        for o in opps:
            title = o.get('Title')
            op_id = o.get('Id')
            if not title or not op_id:
                continue
            job_url = f"https://recruiting.ultipro.com/{tenant}/JobBoard/{board}/OpportunityDetail?opportunityId={op_id}"
            loc = "The Villages, FL"
            locations = o.get('Locations', [])
            if locations:
                loc = locations[0].get('LocalizedDescription', loc)

            jobs.append({
                "Job_Title": title.strip(),
                "Company": company,
                "Estimated_Salary": "Competitive Banking Compensation",
                "Location": loc,
                "Job_Link": job_url,
                "Description": f"Verified banking position with {company}.",
                "Employment_Type": "Full-Time"
            })
    except Exception as e:
        print(f"[UltiPro] Error for {company}: {e}")
    return jobs

# 7. Workstream ATS Driver (e.g. 4 Rivers Smokehouse)
def driver_workstream(feed):
    jobs = []
    slug = feed['slug']
    token = feed['token']
    company = feed['company']
    api_url = f"https://www.workstream.us/j/{token}/{slug}/positions?radius=15&lat=28.7632&lng=-81.9152&page=1"

    try:
        req = urllib.request.Request(api_url, headers=DEFAULT_HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            for a in soup.find_all('a', href=True):
                h = a['href']
                if '/position/' in h:
                    title = a.get_text(strip=True)
                    if title:
                        jobs.append({
                            "Job_Title": title.strip(),
                            "Company": company,
                            "Estimated_Salary": "$14 - $22/hr",
                            "Location": "Middleton / The Villages, FL",
                            "Job_Link": urllib.parse.urljoin("https://www.workstream.us", h),
                            "Description": f"Active restaurant position with {company}.",
                            "Employment_Type": "Full-Time"
                        })
    except Exception as e:
        print(f"[Workstream] Error for {company}: {e}")
    return jobs

# 8. Dayforce HCM Driver via Playwright (e.g. Down To Earth Landscaping)
def driver_dayforce_playwright(feed):
    jobs = []
    portal_url = feed['portal_url']
    company = feed['company']

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(portal_url, wait_until="networkidle", timeout=15000)
            page.wait_for_timeout(2000)

            seen_links = set()
            for a in page.locator("a[href*='/CANDIDATEPORTAL/jobs/']").all():
                href = a.get_attribute("href")
                text = a.inner_text().strip()
                if text and text != "Read More" and href not in seen_links:
                    seen_links.add(href)
                    jobs.append({
                        "Job_Title": text.strip(),
                        "Company": company,
                        "Estimated_Salary": "$16 - $28/hr or Salary (DOE)",
                        "Location": "The Villages, FL",
                        "Job_Link": urllib.parse.urljoin("https://jobs.dayforcehcm.com", href),
                        "Description": f"Active landscaping & golf operations position with {company}.",
                        "Employment_Type": "Full-Time"
                    })
            browser.close()
    except Exception as e:
        print(f"[Dayforce] Error for {company}: {e}")
    return jobs

# 9. Greenhouse Board JSON API Driver (e.g. Toojay's Gourmet Deli)
def driver_greenhouse(feed):
    jobs = []
    board = feed['board']
    company = feed['company']
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs"
    
    try:
        data = fetch_json(url)
        results = data.get('jobs', [])
        filter_locations = feed.get('filter_locations', ['villages', 'wildwood', 'lady lake', 'sumter', 'lake county'])
        
        for item in results:
            loc = item.get('location', {}).get('name', '')
            # If location matches or no location filter specified
            if filter_locations:
                loc_lower = loc.lower()
                if not any(k in loc_lower for k in filter_locations):
                    continue
            
            title = item.get('title')
            if not title:
                continue
            
            jobs.append({
                "Job_Title": title.strip(),
                "Company": company,
                "Estimated_Salary": "$15 - $25/hr or Salary (DOE)",
                "Location": loc or "The Villages, FL",
                "Job_Link": item.get('absolute_url') or f"https://boards.greenhouse.io/{board}",
                "Description": f"Active position with {company}.",
                "Employment_Type": "Full-Time"
            })
    except Exception as e:
        print(f"[Greenhouse] Error for {company}: {e}")
    return jobs

# 10. Paylocity Job Board Driver (e.g. Oak & Stone, Sonny's BBQ)
def driver_paylocity(feed):
    jobs = []
    url = feed['url']
    company = feed['company']
    filter_locations = feed.get('filter_locations', ['villages', 'wildwood', 'lady lake', 'middleton', 'eastport'])

    try:
        req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
        html = urllib.request.urlopen(req, context=SSL_CTX, timeout=12).read().decode('utf-8', errors='ignore')
        m = re.findall(r'window\.[a-zA-Z0-9_]+\s*=\s*(\{.*?\});', html, re.DOTALL)
        for item in m:
            try:
                data = json.loads(item)
                if 'Jobs' in data:
                    for j in data['Jobs']:
                        title = j.get('JobTitle')
                        if not title:
                            continue
                        job_id = j.get('JobId')
                        loc_dict = j.get('JobLocation') or {}
                        city = loc_dict.get('City', '')
                        state = loc_dict.get('State', 'FL')
                        addr = loc_dict.get('Address', '')
                        full_loc = f"{city}, {state}".strip(", ")
                        
                        if filter_locations:
                            search_target = f"{city} {addr} {loc_dict.get('Name', '')}".lower()
                            if not any(k in search_target for k in filter_locations):
                                continue

                        job_url = f"https://recruiting.paylocity.com/recruiting/jobs/Details/{job_id}" if job_id else url
                        jobs.append({
                            "Job_Title": title.strip(),
                            "Company": company,
                            "Estimated_Salary": "$16 - $26/hr or Salary (DOE)",
                            "Location": full_loc or "The Villages, FL",
                            "Job_Link": job_url,
                            "Description": f"Active position with {company}.",
                            "Employment_Type": "Full-Time"
                        })
            except Exception:
                pass
    except Exception as e:
        print(f"[Paylocity] Error for {company}: {e}")
    return jobs

# 11. Schema.org Universal JobPosting Driver
def driver_schema_org(feed):
    jobs = []
    url = feed['url']
    company = feed['company']
    filter_locations = feed.get('filter_locations', ['the villages', 'villages', 'wildwood', 'lady lake', 'sumter'])

    try:
        req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
        html = urllib.request.urlopen(req, context=SSL_CTX, timeout=12).read().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        scripts = soup.find_all('script', type='application/ld+json')
        
        for s in scripts:
            try:
                raw = s.string or s.text
                if not raw or 'JobPosting' not in raw:
                    continue
                data = json.loads(raw.strip())
                items = data if isinstance(data, list) else (data.get('@graph', [data]) if isinstance(data, dict) else [])
                for it in items:
                    if isinstance(it, dict) and it.get('@type') in ['JobPosting', 'http://schema.org/JobPosting']:
                        title = it.get('title') or it.get('name')
                        if not title:
                            continue
                        loc_str = ""
                        loc = it.get('jobLocation')
                        if isinstance(loc, dict):
                            addr = loc.get('address')
                            if isinstance(addr, dict):
                                loc_str = f"{addr.get('addressLocality', '')} {addr.get('addressRegion', '')}".strip()
                            elif isinstance(addr, str):
                                loc_str = addr
                        
                        if filter_locations and loc_str:
                            if not any(k in loc_str.lower() for k in filter_locations):
                                continue

                        job_url = it.get('url') or url
                        if not job_url.startswith('http'):
                            job_url = urllib.parse.urljoin(url, job_url)
                        
                        jobs.append({
                            "Job_Title": title.strip(),
                            "Company": company,
                            "Estimated_Salary": "$18 - $30/hr or Salary (DOE)",
                            "Location": loc_str or "The Villages, FL",
                            "Job_Link": job_url,
                            "Description": (it.get('description') or f"Active position with {company}.")[:300],
                            "Employment_Type": "Full-Time"
                        })
            except Exception:
                pass
    except Exception as e:
        print(f"[Schema.org] Error for {company}: {e}")
    return jobs

# 12. TalentBrew / Radancy Driver (e.g. AT&T, Chili's)
def driver_talentbrew(feed):
    jobs = []
    base_url = feed['base_url']
    company = feed['company']
    locations = feed.get('search_locations', ['Lady Lake, FL'])
    org_id = feed.get('org_id', '117')
    filter_keywords = feed.get('filter_keywords', ['lady lake', 'leesburg', 'villages', 'wildwood', 'sumter'])

    seen_links = set()
    for loc in locations:
        loc_encoded = urllib.parse.quote(loc)
        url = f"{base_url}/search-jobs/{loc_encoded}/{org_id}/1"
        try:
            req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=10) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                soup = BeautifulSoup(html, 'html.parser')
                for a in soup.find_all('a', href=True):
                    h = a['href']
                    if '/job/' in h and h not in seen_links:
                        parent_li = a.find_parent('li')
                        loc_span = parent_li.find('span', class_='job-location') if parent_li else None
                        loc_text = loc_span.get_text(strip=True) if loc_span else ''
                        if filter_keywords and loc_text:
                            if not any(k in loc_text.lower() for k in filter_keywords):
                                continue
                        title = a.get_text(strip=True)
                        if title:
                            seen_links.add(h)
                            full_url = urllib.parse.urljoin(base_url, h)
                            jobs.append({
                                "Job_Title": title,
                                "Company": company,
                                "Estimated_Salary": "$45,000 - $65,000/yr (DOE + Commission)",
                                "Location": loc_text or "The Villages / Lady Lake, FL",
                                "Job_Link": full_url,
                                "Description": f"Active telecommunications sales position with {company}.",
                                "Employment_Type": "Full-Time"
                            })
        except Exception as e:
            print(f"[TalentBrew] Error for {company}: {e}")
    return jobs

PROTOCOL_DISPATCHER = {
    'icims_jibe': driver_icims_jibe,
    'workday_cxs': driver_workday_cxs,
    'adp_wfn': driver_adp_wfn,
    'neogov': driver_neogov,
    'clearcompany_api': driver_clearcompany_api,
    'ultipro_board': driver_ultipro_board,
    'workstream': driver_workstream,
    'dayforce_playwright': driver_dayforce_playwright,
    'greenhouse': driver_greenhouse,
    'paylocity': driver_paylocity,
    'schema_org': driver_schema_org,
    'talentbrew': driver_talentbrew
}

def execute_driver(feed):
    protocol = feed.get('protocol')
    driver = PROTOCOL_DISPATCHER.get(protocol)
    if not driver:
        print(f"Warning: Unknown protocol '{protocol}' for feed '{feed.get('id')}'")
        return []
    return driver(feed)
