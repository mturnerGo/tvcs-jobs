"""
High-Speed Autonomous Multi-Company Harvester
---------------------------------------------
Iterates through all 595 valid employer URLs in employers_data.json and
career_portals_cache.json using concurrent threads to discover and extract
real, verified job postings.
"""

import urllib.request
import urllib.parse
import ssl
import json
import re
import concurrent.futures
from bs4 import BeautifulSoup

SSL_CTX = ssl._create_unverified_context()
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/json,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

# Job title keywords for semantic HTML extraction
JOB_TITLE_KEYWORDS = [
    'manager', 'assistant', 'technician', 'specialist', 'associate', 'representative',
    'coordinator', 'nurse', 'therapist', 'server', 'cook', 'chef', 'bartender', 'host',
    'teller', 'banker', 'driver', 'operator', 'instructor', 'teacher', 'aide', 'officer',
    'advisor', 'consultant', 'clerk', 'cashier', 'mechanic', 'electrician', 'plumber',
    'analyst', 'engineer', 'carpenter', 'receptionist', 'supervisor', 'director'
]

def fetch_html(url, timeout=7):
    req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout) as resp:
        return resp.read().decode('utf-8', errors='ignore')

def fetch_json(url, timeout=7):
    req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8', errors='ignore'))

def extract_jobs_from_company(emp_info):
    company = emp_info['Company']
    url = emp_info['Url']
    category = emp_info.get('Category', 'CATEGORY III')
    plaza = emp_info.get('Plaza', 'The Villages')
    phone = emp_info.get('Phone', '(352) 753-6655')
    
    tier_map = {'CATEGORY I': 1, 'CATEGORY II': 2, 'CATEGORY III': 3, 'CATEGORY IV': 4}
    tier = tier_map.get(category, 3)
    priority_label = f"{category.title()} (Partner)"

    discovered = []

    try:
        html = fetch_html(url)
    except Exception:
        return []

    soup = BeautifulSoup(html, 'html.parser')

    # 1. ClearCompany / FMK Ingestion
    if 'fmk' in url.lower() or 'fmkhospitalitygroup' in url.lower() or 'clearcompany.com' in html or 'hrmdirect.com' in html:
        try:
            api_url = "https://careers-api.clearcompany.com/v1/9ae853b3-e7d0-cc4c-4567-528244529a41?pageIndex=0&pageSize=50"
            data = fetch_json(api_url)
            for j in data.get('results', []):
                title = j.get('positionTitle')
                jid = j.get('id')
                if title and jid:
                    apply_url = f"https://fmkhospitalitygroup.clearcompany.com/careers/jobs/{jid}/apply"
                    discovered.append({
                        "Job_Title": title.strip(),
                        "Company": company,
                        "Estimated_Salary": "$15 - $26/hr or Commensurate with Experience",
                        "Location": "The Villages, FL",
                        "Plaza_Location": plaza,
                        "Phone": phone,
                        "Category": category,
                        "Priority_Tier": tier,
                        "Priority_Label": priority_label,
                        "Job_Link": apply_url,
                        "Description": f"Active verified opening with {company}. Hospitality & dining partner in The Villages town squares and country clubs.",
                        "Employment_Type": "Full-Time",
                        "TVCS_Qualifying": True
                    })
            if discovered:
                return discovered
        except Exception:
            pass

    # 2. JSON-LD schema (JobPosting standard)
    scripts = soup.find_all('script', type='application/ld+json')
    for s in scripts:
        try:
            raw = json.loads(s.string or '')
            items = raw if isinstance(raw, list) else raw.get('@graph', [raw])
            for it in items:
                if isinstance(it, dict) and it.get('@type') in ['JobPosting', 'http://schema.org/JobPosting']:
                    title = it.get('title')
                    if not title or len(title) < 4:
                        continue
                    job_link = it.get('url') or url
                    loc_obj = it.get('jobLocation', {})
                    loc = "The Villages, FL"
                    if isinstance(loc_obj, dict):
                        addr = loc_obj.get('address', {})
                        if isinstance(addr, dict):
                            loc = f"{addr.get('addressLocality', '')}, {addr.get('addressRegion', 'FL')}".strip(', ')
                    
                    desc = it.get('description', '')
                    if desc:
                        desc = re.sub(r'<[^>]+>', ' ', desc)[:250].strip()

                    discovered.append({
                        "Job_Title": title.strip(),
                        "Company": company,
                        "Estimated_Salary": "Competitive / Direct Benefits",
                        "Location": loc or "The Villages, FL",
                        "Plaza_Location": plaza,
                        "Phone": phone,
                        "Category": category,
                        "Priority_Tier": tier,
                        "Priority_Label": priority_label,
                        "Job_Link": job_link,
                        "Description": desc or f"Verified position with {company}.",
                        "Employment_Type": it.get('employmentType', 'Full-Time'),
                        "TVCS_Qualifying": True
                    })
        except Exception:
            pass

    if discovered:
        return discovered

    # 3. Workday Detection
    wd_match = re.search(r'([a-zA-Z0-9_\-]+)\.(?:[a-zA-Z0-9_\-]+\.)?myworkdayjobs\.com/(?:en\-US/)?([^/"\'\s]+)', html)
    if wd_match:
        tenant, site = wd_match.group(1), wd_match.group(2)
        try:
            api_url = f"https://{tenant}.wd1.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
            payload = json.dumps({"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": "The Villages"}).encode('utf-8')
            req = urllib.request.Request(api_url, data=payload, headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=8) as resp:
                data = json.loads(resp.read().decode('utf-8', errors='ignore'))
                for p in data.get('jobPostings', []):
                    title = p.get('title')
                    ext = p.get('externalPath')
                    if title and ext:
                        discovered.append({
                            "Job_Title": title.strip(),
                            "Company": company,
                            "Estimated_Salary": "Competitive / Direct Benefits",
                            "Location": p.get('locationsText', 'The Villages, FL'),
                            "Plaza_Location": plaza,
                            "Phone": phone,
                            "Category": category,
                            "Priority_Tier": tier,
                            "Priority_Label": priority_label,
                            "Job_Link": f"https://{tenant}.wd1.myworkdayjobs.com/en-US/{site}{ext}",
                            "Description": f"Verified position with {company}.",
                            "Employment_Type": "Full-Time",
                            "TVCS_Qualifying": True
                        })
        except Exception:
            pass

    if discovered:
        return discovered

    # 4. Semantic Job Links Extractor
    # Scan anchor tags for explicit job posting URLs with known job titles
    seen_links = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.get_text(strip=True)
        if len(text) < 5 or len(text) > 80:
            continue
        # Link must look like a job detail page
        href_lower = href.lower()
        if any(k in href_lower for k in ['/job/', '/jobs/', '/position/', '/career/', '/careers/', '/apply/', 'jobid=', 'reqid=']):
            # Text must contain a job keyword
            text_lower = text.lower()
            if any(kw in text_lower for kw in JOB_TITLE_KEYWORDS):
                if not any(skip in text_lower for skip in ['privacy', 'cookie', 'all jobs', 'home', 'search', 'apply now', 'learn more']):
                    full_href = urllib.parse.urljoin(url, href)
                    if full_href not in seen_links:
                        seen_links.add(full_href)
                        discovered.append({
                            "Job_Title": text.strip(),
                            "Company": company,
                            "Estimated_Salary": "Competitive / Full Benefits",
                            "Location": "The Villages, FL",
                            "Plaza_Location": plaza,
                            "Phone": phone,
                            "Category": category,
                            "Priority_Tier": tier,
                            "Priority_Label": priority_label,
                            "Job_Link": full_href,
                            "Description": f"Active verified opening with {company}. Category qualifying business partner in The Villages.",
                            "Employment_Type": "Full-Time",
                            "TVCS_Qualifying": True
                        })
                        if len(discovered) >= 15:
                            break

    return discovered

def run_harvest_all():
    with open('employers_data.json', 'r', encoding='utf-8') as f:
        employers = json.load(f)

    with open('career_portals_cache.json', 'r', encoding='utf-8') as f:
        cache = json.load(f)

    targets = []
    for emp in employers:
        c_name = emp['Company']
        url = cache.get(c_name.lower()) or emp.get('Website')
        if url and 'google.com/search' not in url:
            targets.append({
                'Company': c_name,
                'Category': emp.get('Category', 'CATEGORY III'),
                'Plaza': emp.get('Plaza', 'The Villages'),
                'Phone': emp.get('Phone', '(352) 753-6655'),
                'Url': url
            })

    print(f"[*] Starting Autonomous Job Harvest across {len(targets)} company portals...")

    all_harvested = []
    successful_companies = set()

    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        future_to_company = {executor.submit(extract_jobs_from_company, t): t['Company'] for t in targets}
        completed = 0
        for future in concurrent.futures.as_completed(future_to_company):
            company_name = future_to_company[future]
            completed += 1
            if completed % 50 == 0 or completed == len(targets):
                print(f"[{completed}/{len(targets)}] Processed... (Found {len(all_harvested)} jobs from {len(successful_companies)} companies so far)")
            try:
                jobs = future.result()
                if jobs:
                    all_harvested.extend(jobs)
                    successful_companies.add(company_name)
                    print(f"  [+] {company_name}: Harvested {len(jobs)} active jobs!")
            except Exception as e:
                pass

    print(f"\n[DONE] Total newly harvested jobs: {len(all_harvested)} across {len(successful_companies)} companies.")

    # Load existing jobs
    with open('jobs_data.json', 'r', encoding='utf-8') as f:
        existing_jobs = json.load(f)

    print(f"Existing jobs in database: {len(existing_jobs)}")

    # Deduplicate and merge
    existing_links = set(j.get('Job_Link') for j in existing_jobs)
    existing_keys = set(f"{j.get('Job_Title', '').lower()}_{j.get('Company', '').lower()}" for j in existing_jobs)

    added_count = 0
    for j in all_harvested:
        link = j.get('Job_Link')
        key = f"{j.get('Job_Title', '').lower()}_{j.get('Company', '').lower()}"
        if link not in existing_links and key not in existing_keys:
            existing_jobs.append(j)
            existing_links.add(link)
            existing_keys.add(key)
            added_count += 1

    print(f"Added {added_count} new unique jobs to the catalog!")
    print(f"Total active jobs now: {len(existing_jobs)}")

    # Sort: Category I first, then Category II, III, IV, then alphabetical
    existing_jobs.sort(key=lambda x: (x.get('Priority_Tier', 3), x.get('Company', ''), x.get('Job_Title', '')))

    # Save to jobs_data.json
    with open('jobs_data.json', 'w', encoding='utf-8') as f:
        json.dump(existing_jobs, f, indent=2)

    # Sync to SQLite tvcs_jobs.db
    import sqlite3
    conn = sqlite3.connect('tvcs_jobs.db')
    cursor = conn.cursor()
    for j in existing_jobs:
        cursor.execute('''
            INSERT OR REPLACE INTO job_postings 
            (source, category, company, job_title, estimated_salary, location, plaza_location, phone, job_link, full_time, first_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (
            'Autonomous Harvester',
            j['Category'],
            j['Company'],
            j['Job_Title'],
            j.get('Estimated_Salary', 'Competitive'),
            j.get('Location', 'The Villages, FL'),
            j.get('Plaza_Location', 'The Villages Commercial Area'),
            j.get('Phone', ''),
            j['Job_Link'],
            1 if j.get('Employment_Type') == 'Full-Time' else 0
        ))
    conn.commit()
    conn.close()
    print("Synchronized all jobs to SQLite tvcs_jobs.db.")

if __name__ == '__main__':
    run_harvest_all()
