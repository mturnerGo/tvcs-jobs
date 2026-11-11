import asyncio
import os
import re
import json
import sqlite3
import urllib.request
import urllib.parse
import ssl
import pandas as pd
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

CSV_CATALOG_FILE = "all_tvcs_employers_with_links.csv"
JOBS_OUTPUT_FILE = "jobs_data.json"
EMPLOYERS_OUTPUT_FILE = "employers_data.json"
CACHE_FILE = "career_portals_cache.json"
DB_FILE = "tvcs_jobs.db"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*'
}

TVCS_API_URL = "https://api.v2.thevillages.com/tvcs/marketplace"
TVCS_API_AUTH = "Basic 66b4f35545eb13db7521380a"

KNOWN_ATS_DOMAINS = [
    "workstream.us", "myworkdayjobs.com", "greenhouse.io", "lever.co",
    "adp.com", "icims.com", "paylocity.com", "bamboohr.com", "applytojob.com",
    "talentreef.com", "taleo.net", "governmentjobs.com", "smartrecruiters.com"
]

# Comprehensive Brand to Verified Geo-Career Portal Mapping for The Villages Region
BRAND_CAREERS_MAP = {
    "4 rivers": "https://www.workstream.us/j/277e58a2/4-rivers-smokehouse/positions?locale=en&referer_source=https%3A%2F%2Fwww.4rsmokehouse.com%2F&page=1&radius=10&lat=28.76320339999999&lng=-81.91528439999999&geo=Okahumpka%2C%20FL%2034762%2C%20USA",
    "another broken egg": "https://www.anotherbrokenegg.com/employment-jobs/",
    "applebee": "https://www.applebees.com/en/careers",
    "adventhealth": "https://www.adventhealth.com/careers",
    "advent health": "https://www.adventhealth.com/careers",
    "advanced derm": "https://www.advancedderm.com/join-us/careers",
    "adv derm": "https://www.advancedderm.com/join-us/careers",
    "bank of america": "https://careers.bankofamerica.com/",
    "barnes & noble": "https://careers.barnesandnoble.com/",
    "bb&t": "https://careers.truist.com/",
    "bonefish": "https://www.bonefishgrill.com/careers",
    "brownwood hotel": "https://www.brownwoodhotelandspa.com/careers",
    "bushnell truss": "https://bushnelltruss.com/",
    "chase": "https://careers.jpmorganchase.com/",
    "chick-fil-a": "https://www.chick-fil-a.com/careers/team-member-employment/employment-opportunities",
    "chicken salad chick": "https://www.chickensaladchick.com/careers/",
    "chili": "https://www.chilisjobs.com/",
    "chipotle": "https://jobs.chipotle.com/",
    "citizens first": "https://www.seacoastbank.com/careers",
    "city fire": "https://www.cityfirerestaurants.com/careers",
    "culver": "https://www.culvers.com/careers",
    "cvs": "https://jobs.cvshealth.com/",
    "dunkin": "https://careers.dunkindonuts.com/",
    "edward jones": "https://careers.edwardjones.com/",
    "flippers": "https://flipperspizzeria.com/careers/",
    "jacobs": "https://jacobs.jobs/locations/the-villages-fl/jobs/",
    "labcorp": "https://careers.labcorp.com/",
    "miller's ale house": "https://millersalehouse.com/careers/",
    "outback": "https://www.outback.com/careers",
    "panera": "https://careers.panerabread.com/",
    "properties of the villages": "https://www.thevillages.com/careers/search/",
    "publix": "https://jobs.publix.com/",
    "quest diagnostics": "https://careers.questdiagnostics.com/",
    "rainey construction": "https://raineyconstruction.com/careers/",
    "red sauce": "https://redsaucefl.com/careers/",
    "ro-mac lumber": "https://romaclumber.com/careers/",
    "seacoast": "https://www.seacoastbank.com/careers",
    "starbucks": "https://www.starbucks.com/careers/",
    "strada": "https://stradaservices.com/careers/",
    "subway": "https://www.subway.com/en-us/careers",
    "sumter county bocc": "https://www.governmentjobs.com/careers/sumtercountyfl",
    "sun kool": "https://sunkool.com/careers/",
    "target": "https://corporate.target.com/careers",
    "the villages charter school": "https://www.thevillages.com/careers/search/filter/cat:18/?category=18",
    "the villages early childhood": "https://www.thevillages.com/careers/search/",
    "the villages equipment": "https://www.thevillages.com/careers/search/",
    "the villages golf cars": "https://thevillagesgolfcars.com/careers/",
    "the villages land operating": "https://www.thevillages.com/careers/search/",
    "the villages of lake-sumter": "https://www.thevillages.com/careers/search/",
    "the villages technology": "https://www.thevillages.com/careers/search/",
    "tierra del sol": "https://www.thevillages.com/careers/search/",
    "topeekeegee": "https://www.thevillages.com/careers/search/",
    "truist": "https://careers.truist.com/",
    "ubreakifix": "https://www.ubreakifix.com/careers",
    "uf health": "https://jobs.ufhealth.org/",
    "walgreens": "https://jobs.walgreens.com/",
    "walgreen": "https://jobs.walgreens.com/",
    "wells fargo": "https://www.wellsfargojobs.com/",
    "winn-dixie": "https://www.winndixie.com/careers",
    "winn dixie": "https://www.winndixie.com/careers",
    "world of beer": "https://worldofbeer.com/careers/"
}


def load_career_cache():
    cache = dict(BRAND_CAREERS_MAP)
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                disk_cache = json.load(f)
                cache.update(disk_cache)
        except Exception:
            pass
    return cache


def save_career_cache(cache):
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"      [!] Failed to save cache: {e}")


def clean_company_name(raw_name):
    if not raw_name or pd.isna(raw_name):
        return ""
    name = re.sub(r"(?i)\b(inc|llc|corp|ltd|co|group|dba|pa|pllc|the|florida|solutions)\b\.?", "", str(raw_name))
    name = re.sub(r"[^\w\s]", "", name)
    return " ".join(name.strip().split())


def format_phone(phone_raw):
    if not phone_raw or pd.isna(phone_raw):
        return ""
    digits = re.sub(r'\D', '', str(phone_raw))
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits.startswith('1'):
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    return str(phone_raw).strip()


FREE_EMAIL_DOMAINS = {
    'gmail.com', 'yahoo.com', 'aol.com', 'comcast.net', 'outlook.com',
    'hotmail.com', 'icloud.com', 'msn.com', 'sbcglobal.net', 'me.com',
    'bellsouth.net', 'verizon.net', 'cfl.rr.com', 'earthlink.net',
    'embarqmail.com', 'att.net', 'cox.net', 'charter.net'
}

def resolve_direct_career_url(comp_name, web_raw, plaza_name, cache, email_raw=""):
    """Resolves the most accurate Careers / ATS URL for an employer with geo-intent."""
    clean_key = comp_name.strip()
    c_lower = clean_key.lower()

    # 1. Exact match in cache
    if clean_key in cache:
        return cache[clean_key], True

    # 2. Check Brand Keywords (Panera, Starbucks, 4 Rivers, Publix, etc.)
    for brand_kw, career_url in cache.items():
        if brand_kw.lower() in c_lower:
            cache[clean_key] = career_url
            return career_url, True

    for brand_kw, career_url in BRAND_CAREERS_MAP.items():
        if brand_kw in c_lower:
            cache[clean_key] = career_url
            return career_url, True

    # 3. Check if company provided an official website in TVCS database
    w = str(web_raw).strip() if web_raw and not pd.isna(web_raw) else ""
    if w and w.lower() not in ['none', 'nan', 'null', 'n/a', 'no', '']:
        base_url = w if w.startswith('http://') or w.startswith('https://') else f"https://{w}"
        cache[clean_key] = base_url
        return base_url, True

    # 4. Check if company has an official corporate email domain
    if email_raw and '@' in str(email_raw):
        dom = str(email_raw).split('@')[-1].lower().strip()
        if dom and dom not in FREE_EMAIL_DOMAINS and '.' in dom:
            email_site = f"https://www.{dom}"
            cache[clean_key] = email_site
            return email_site, True

    # 5. Geo-Targeted Careers Search Fallback (Scoped specifically to The Villages/Middleton/Plaza)
    geo_plaza = plaza_name if plaza_name and plaza_name != "The Villages Commercial Area" else "The Villages"
    q = urllib.parse.quote(f'"{comp_name}" "{geo_plaza}" Florida careers jobs employment application')
    fallback_url = f"https://www.google.com/search?q={q}"
    return fallback_url, False


def determine_category_priority(cat_val):
    cat_str = str(cat_val).upper().strip()
    if cat_str in ["1", "I", "CATEGORY 1", "CATEGORY I"]:
        return 1, "CATEGORY I", "Category I (Direct - 1st Priority)"
    elif cat_str in ["2", "II", "CATEGORY 2", "CATEGORY II"]:
        return 2, "CATEGORY II", "Category II (Subcontractor - 2nd Priority)"
    elif cat_str in ["3", "III", "CATEGORY 3", "CATEGORY III"]:
        return 3, "CATEGORY III", "Category III (Commercial Tenant - 3rd Priority)"
    elif cat_str in ["4", "IV", "CATEGORY 4", "CATEGORY IV"]:
        return 4, "CATEGORY IV", "Category IV (Approved Vendor - 4th Priority)"
    return 3, "CATEGORY III", "Category III (Commercial Tenant - 3rd Priority)"


def is_full_time(title_str, work_type_str=""):
    combined = f"{title_str} {work_type_str}".lower()
    if any(pt in combined for pt in ["part-time", "part time", "prn", "substitute", "temporary", "temp "]):
        return False
    return True


# ---------------------------------------------------------------------------
# 1. Harvest The Villages Charter School (TVCS) Direct Positions (Category I)
# ---------------------------------------------------------------------------
def harvest_tvcs_jobs():
    print("\n[1/5] Harvesting The Villages Charter School (TVCS) Requisitions...")
    jobs = []
    tvcs_cid = "9d9691d5-3462-4689-a406-011d044de96e"
    api_url = f"https://workforcenow.adp.com/mascsr/default/careercenter/public/events/staffing/v1/job-requisitions?cid={tvcs_cid}&timeStamp=1000"
    try:
        req = urllib.request.Request(api_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for req_item in data.get('jobRequisitions', []):
                title = req_item.get('requisitionTitle', '').strip()
                item_id = req_item.get('itemID', '')
                if not title or not item_id:
                    continue

                full_time = is_full_time(title)
                campus = "Buffalo Ridge Campus" if "buffalo" in title.lower() else ("Middleton Campus" if "middleton" in title.lower() else "All TVCS Campuses")
                apply_link = f"https://workforcenow.adp.com/mascsr/default/mdf/recruitment/recruitment.html?cid={tvcs_cid}&jobId={item_id}"
                
                jobs.append({
                    "Job_Title": title,
                    "Company": "The Villages Charter School",
                    "Category": "CATEGORY I",
                    "Priority_Tier": 1,
                    "Priority_Label": "Category I (Direct - 1st Priority)",
                    "Employment_Type": "Full-Time" if full_time else "Part-Time",
                    "TVCS_Qualifying": full_time,
                    "Plaza_Location": f"TVCS {campus}",
                    "Location": "The Villages, FL",
                    "Phone": "(352) 259-2350",
                    "Estimated_Salary": "TVCS Instructional/Staff Scale + Benefits" if full_time else "Hourly Scale",
                    "Source": "The Villages Charter School (Official ATS)",
                    "Job_Link": apply_link,
                    "Posted_Date": req_item.get('postDate', '')[:10] if req_item.get('postDate') else "Recent",
                    "Description": f"Official position at The Villages Charter School ({campus}). Full-time positions qualify dependents for Category I TVCS enrollment priority."
                })
        print(f"      ✓ TVCS: Captured {len(jobs)} active school positions.")
    except Exception as e:
        print(f"      [!] Error harvesting TVCS jobs: {e}")
    return jobs


# ---------------------------------------------------------------------------
# 2. Harvest The Villages Operating Entities Positions (Category I)
# ---------------------------------------------------------------------------
def harvest_the_villages_operating_jobs():
    print("\n[2/5] Harvesting The Villages Operating Entities...")
    jobs = []
    v_cid = "ea774d00-96ec-4432-b137-9f604cbb5c8e"
    api_url = f"https://workforcenow.adp.com/mascsr/default/careercenter/public/events/staffing/v1/job-requisitions?cid={v_cid}&timeStamp=1000"
    try:
        req = urllib.request.Request(api_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for req_item in data.get('jobRequisitions', []):
                title = req_item.get('requisitionTitle', '').strip()
                item_id = req_item.get('itemID', '')
                if not title or not item_id:
                    continue

                full_time = is_full_time(title)
                locs = req_item.get('requisitionLocations', [])
                loc_name = "The Villages, FL"
                plaza = "The Villages Commercial Area"
                if locs and 'nameCode' in locs[0]:
                    loc_name = locs[0]['nameCode'].get('shortName', 'The Villages, FL').strip()
                
                t_lower = title.lower()
                if "lake sumter" in t_lower:
                    plaza = "Lake Sumter Landing"
                elif "spanish springs" in t_lower:
                    plaza = "Spanish Springs"
                elif "brownwood" in t_lower:
                    plaza = "Brownwood Paddock Square"
                elif "middleton" in t_lower or "middleton" in loc_name.lower():
                    plaza = "Middleton Downtown"
                elif "eastport" in t_lower:
                    plaza = "Eastport Town Center"

                apply_link = f"https://workforcenow.adp.com/mascsr/default/mdf/recruitment/recruitment.html?cid={v_cid}&jobId={item_id}"
                
                jobs.append({
                    "Job_Title": title,
                    "Company": "The Villages Operating Entities",
                    "Category": "CATEGORY I",
                    "Priority_Tier": 1,
                    "Priority_Label": "Category I (Direct - 1st Priority)",
                    "Employment_Type": "Full-Time" if full_time else "Part-Time",
                    "TVCS_Qualifying": full_time,
                    "Plaza_Location": plaza,
                    "Location": loc_name,
                    "Phone": "(352) 753-6655",
                    "Estimated_Salary": "Competitive Enterprise Scale + Benefits" if full_time else "Hourly Scale",
                    "Source": "The Villages Careers (Official ATS)",
                    "Job_Link": apply_link,
                    "Posted_Date": req_item.get('postDate', '')[:10] if req_item.get('postDate') else "Recent",
                    "Description": f"Direct position with The Villages Operating Entities in {plaza}. Full-time employees receive Category I enrollment eligibility."
                })
        print(f"      ✓ The Villages: Captured {len(jobs)} active positions.")
    except Exception as e:
        print(f"      [!] Error harvesting The Villages operating jobs: {e}")
    return jobs


# ---------------------------------------------------------------------------
# 3. Harvest Sumter County BOCC Public Jobs (Category II)
# ---------------------------------------------------------------------------
def harvest_sumter_county_jobs():
    print("\n[3/6] Harvesting Sumter County BOCC (Category II)...")
    jobs = []
    gov_url = 'https://www.governmentjobs.com/careers/home/index?agency=sumtercountyfl&sort=PositionTitle&isDescendingSort=false'
    gov_headers = dict(HEADERS)
    gov_headers['X-Requested-With'] = 'XMLHttpRequest'
    try:
        req = urllib.request.Request(gov_url, headers=gov_headers)
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(content, 'html.parser')
            for a in soup.select('a[href*="/careers/sumtercountyfl/jobs/"]'):
                title = a.get_text().strip()
                href = a.get('href', '')
                if not title or not href:
                    continue
                link = href if href.startswith('http') else f"https://www.governmentjobs.com{href}"
                if any(x['Job_Link'] == link for x in jobs):
                    continue

                full_time = is_full_time(title)
                jobs.append({
                    "Job_Title": title,
                    "Company": "Sumter County BOCC",
                    "Category": "CATEGORY II",
                    "Priority_Tier": 2,
                    "Priority_Label": "Category II (Subcontractor - 2nd Priority)",
                    "Employment_Type": "Full-Time" if full_time else "Part-Time",
                    "TVCS_Qualifying": full_time,
                    "Plaza_Location": "Sumter County Government Complex",
                    "Location": "The Villages / Sumter County, FL",
                    "Phone": "(352) 689-4400",
                    "Estimated_Salary": "County Public Scale & FRS Pension",
                    "Source": "GovernmentJobs (NEOGOV)",
                    "Job_Link": link,
                    "Posted_Date": "Active Requisition",
                    "Description": "Sumter County Board of County Commissioners operational support role. Full-time continuous positions qualify for TVCS Category II admission."
                })
        print(f"      ✓ Sumter County: Captured {len(jobs)} active positions.")
    except Exception as e:
        print(f"      [!] Error harvesting Sumter County jobs: {e}")
    return jobs


# ---------------------------------------------------------------------------
# 3b. Harvest Village Center Community Development District (VCCDD - Category II)
# ---------------------------------------------------------------------------
def harvest_vccdd_jobs():
    print("\n[3b/6] Harvesting Village Center Community Dev. District (VCCDD - Category II)...")
    jobs = []
    vccdd_cid = "c804bf4f-d461-4f38-861c-c50199110eeb"
    api_url = f"https://workforcenow.adp.com/mascsr/default/careercenter/public/events/staffing/v1/job-requisitions?cid={vccdd_cid}&timeStamp=1000"
    try:
        req = urllib.request.Request(api_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for req_item in data.get('jobRequisitions', []):
                title = req_item.get('requisitionTitle', '').strip()
                item_id = req_item.get('itemID', '')
                if not title or not item_id:
                    continue

                full_time = is_full_time(title)
                locs = req_item.get('requisitionLocations', [])
                loc_name = "The Villages, FL"
                if locs and 'nameCode' in locs[0]:
                    nc = locs[0]['nameCode']
                    loc_name = nc.get('shortName', 'The Villages, FL').strip() if isinstance(nc, dict) else "The Villages, FL"

                apply_link = f"https://workforcenow.adp.com/mascsr/default/mdf/recruitment/recruitment.html?cid={vccdd_cid}&jobId={item_id}"
                t_lower = title.lower()
                dept = "Public Safety & Fire Rescue" if any(k in t_lower for k in ['fire', 'paramedic', 'captain']) else ("Recreation & Golf Maintenance" if any(k in t_lower for k in ['recreation', 'staff', 'outside']) else "District Government Administration")
                
                jobs.append({
                    "Job_Title": title.title(),
                    "Company": "Village Center Community Dev. District",
                    "Category": "CATEGORY II",
                    "Priority_Tier": 2,
                    "Priority_Label": "Category II (Subcontractor - 2nd Priority)",
                    "Employment_Type": "Full-Time" if full_time else "Part-Time",
                    "TVCS_Qualifying": full_time,
                    "Plaza_Location": f"VCCDD - {dept}",
                    "Location": loc_name,
                    "Phone": "(352) 751-3939",
                    "Estimated_Salary": "District Public Scale + Benefits" if full_time else "Competitive Hourly Scale",
                    "Source": "VCCDD District Gov (Official ADP ATS)",
                    "Job_Link": apply_link,
                    "Posted_Date": req_item.get('postDate', '')[:10] if req_item.get('postDate') else "Recent",
                    "Description": f"Official position with Village Center Community Development District ({dept}). Full-time continuous positions qualify dependents for Category II admission."
                })
        print(f"      ✓ VCCDD District Gov: Captured {len(jobs)} active positions.")
    except Exception as e:
        print(f"      [!] Error harvesting VCCDD jobs: {e}")
    return jobs


# ---------------------------------------------------------------------------
# 4. Harvest Jacobs Engineering (Category II)
# ---------------------------------------------------------------------------
async def harvest_jacobs_jobs(browser):
    print("\n[4/5] Harvesting Jacobs Engineering & Infrastructure (Category II)...")
    jobs = []
    page = await browser.new_page()
    try:
        await page.goto("https://jacobs.jobs/locations/the-villages-fl/jobs/", wait_until="domcontentloaded", timeout=25000)
        await page.wait_for_timeout(3000)
        raw_list = await page.evaluate('''() => {
            const list = [];
            document.querySelectorAll('li.job, div.job-card, tr.job-row, a[href*="/job/"]').forEach(el => {
                const titleEl = el.querySelector('h3, h2, a') || el;
                const title = titleEl.innerText ? titleEl.innerText.trim() : '';
                const href = el.getAttribute('href') || (el.querySelector('a') ? el.querySelector('a').getAttribute('href') : '');
                if (title && href && title.length < 90 && !title.toLowerCase().includes('filter')) {
                    list.push({ title: title.split('\\n')[0], url: href.startsWith('http') ? href : `https://jacobs.jobs${href}` });
                }
            });
            return list;
        }''')
        for item in raw_list:
            title = item['title']
            url = item['url']
            if any(x['Job_Link'] == url for x in jobs):
                continue
            full_time = is_full_time(title)
            jobs.append({
                "Job_Title": title,
                "Company": "Jacobs Engineering & Utilities",
                "Category": "CATEGORY II",
                "Priority_Tier": 2,
                "Priority_Label": "Category II (Subcontractor - 2nd Priority)",
                "Employment_Type": "Full-Time" if full_time else "Part-Time",
                "TVCS_Qualifying": full_time,
                "Plaza_Location": "The Villages Utility Operations",
                "Location": "The Villages, FL",
                "Phone": "(352) 753-1756",
                "Estimated_Salary": "Competitive Engineering / Technical Scale",
                "Source": "Jacobs Official ATS",
                "Job_Link": url,
                "Posted_Date": "Active Requisition",
                "Description": "Jacobs direct operational utility and engineering subcontracting for The Villages. Qualifies for Category II admission."
            })
        print(f"      ✓ Jacobs: Captured {len(jobs)} active positions.")
    except Exception as e:
        print(f"      [!] Error harvesting Jacobs jobs: {e}")
    finally:
        await page.close()
    return jobs


# ---------------------------------------------------------------------------
# 5. Harvest 4 Rivers Smokehouse Active Positions (Workstream ATS - Category III)
# ---------------------------------------------------------------------------
def harvest_four_rivers_jobs():
    print("\n[5/6] Harvesting 4 Rivers Smokehouse (Workstream ATS - Category III)...")
    jobs = []
    url = "https://www.workstream.us/j/277e58a2/4-rivers-smokehouse/positions?locale=en&referer_source=https%3A%2F%2Fwww.4rsmokehouse.com%2F&page=1&radius=10&lat=28.76320339999999&lng=-81.91528439999999&geo=Okahumpka%2C%20FL%2034762%2C%20USA"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            for a in soup.find_all('a'):
                href = a.get('href', '')
                if '/middleton-77464/' in href and not href.endswith('/middleton-77464?locale=en'):
                    title = a.get_text(' ', strip=True)
                    if not title or any(j['Job_Link'] == href for j in jobs):
                        continue

                    card = a.find_parent('div', class_=lambda c: c and any(x in c.lower() for x in ['card', 'item', 'position'])) or a.parent
                    card_text = ' '.join(card.stripped_strings) if card else ''

                    pay_match = re.search(r'\$[\d\.,]+\s*(?:-\s*[\d\.,]+)?\s*(?:per\s+hour|per\s+year|/hr|/yr)?', card_text, re.I)
                    salary = pay_match.group(0).strip() if pay_match else ("Competitive Manager Salary + Benefits" if "manager" in title.lower() else "Competitive Hourly + Tips")
                    full_time = "full-time" in card_text.lower() or "manager" in title.lower()

                    jobs.append({
                        "Job_Title": f"4 Rivers Smokehouse - {title}",
                        "Company": "4 Rivers Smokehouse",
                        "Category": "CATEGORY III",
                        "Priority_Tier": 3,
                        "Priority_Label": "Category III (Commercial Tenant - 3rd Priority)",
                        "Employment_Type": "Full-Time" if full_time else "Part-Time",
                        "TVCS_Qualifying": full_time,
                        "Plaza_Location": "Middleton Downtown",
                        "Location": "7679 Middleton Dr, Middleton, FL 34762",
                        "Phone": "(352) 654-1185",
                        "Estimated_Salary": salary,
                        "Source": "Workstream (Official ATS)",
                        "Job_Link": href,
                        "Posted_Date": "Active Requisition",
                        "Description": f"4 Rivers Smokehouse position at 7679 Middleton Dr, Middleton, FL 34762. {'Full-time continuous employment qualifies dependents for TVCS Category III admission.' if full_time else 'Part-time position.'}"
                    })
        print(f"      ✓ 4 Rivers: Captured {len(jobs)} active positions.")
    except Exception as e:
        print(f"      [!] Error harvesting 4 Rivers jobs: {e}")
    return jobs


# ---------------------------------------------------------------------------
# 6. Harvest TVCS Official Marketplace & Resolve Direct Career URLs
# ---------------------------------------------------------------------------
def harvest_official_tvcs_marketplace(active_jobs, cache):
    print("\n[6/6] Harvesting Official TVCS Marketplace & Resolving Direct Career URLs...")
    employers = []
    
    # Map active jobs by company
    job_counts = {}
    for j in active_jobs:
        comp = j['Company'].lower()
        job_counts[comp] = job_counts.get(comp, 0) + 1

    try:
        req = urllib.request.Request(TVCS_API_URL, headers={
            'User-Agent': HEADERS['User-Agent'],
            'Accept': 'application/json, text/plain, */*',
            'Authorization': TVCS_API_AUTH
        })
        with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
            raw_text = resp.read().decode('utf-8', errors='replace')
            data = json.loads(raw_text)
            print(f"      ✓ Retrieved {len(data)} businesses from official TVCS database.")

            resolved_careers_count = 0
            for b in data:
                comp_name = str(b.get('companyName', '')).strip()
                if not comp_name:
                    continue

                plaza = str(b.get('location', '')).strip() or "The Villages Commercial Area"
                phone_raw = b.get('phone', '')
                phone_formatted = format_phone(phone_raw)
                phone_tel = re.sub(r'\D', '', str(phone_raw))
                
                web_raw = b.get('webAddress', '')
                email_raw = str(b.get('email', '') or b.get('verifyEmail', '')).strip()
                contact_raw = str(b.get('contactName', '') or b.get('verifyContact', '')).strip()
                
                # Resolve direct career page or official website
                career_url, has_direct = resolve_direct_career_url(comp_name, web_raw, plaza, cache, email_raw)
                if has_direct:
                    resolved_careers_count += 1

                street = str(b.get('address', '')).strip()
                city = str(b.get('city', 'The Villages')).strip()
                state = str(b.get('state', 'FL')).strip()
                zip_code = str(b.get('postalCode', '')).strip()
                full_address = f"{street}, {city}, {state} {zip_code}".strip(", ") if street else f"{city}, {state}"

                tier_num, cat_code, tier_label = determine_category_priority(b.get('category', '3'))
                is_hiring = str(b.get('isHiring', 'N')).upper().strip() == 'Y'

                clean = clean_company_name(comp_name)

                # Match active jobs count
                active_count = 0
                for comp_key, count in job_counts.items():
                    if clean in comp_key or comp_name.lower() in comp_key or comp_key in comp_name.lower():
                        active_count += count

                employers.append({
                    "Employer_ID": b.get('employerId'),
                    "Company": comp_name,
                    "Category": cat_code,
                    "Priority_Tier": tier_num,
                    "Priority_Label": tier_label,
                    "Plaza": plaza,
                    "Address": full_address,
                    "Phone": phone_formatted,
                    "Phone_Tel": phone_tel,
                    "Website": career_url,
                    "Has_Official_Website": has_direct,
                    "Email": email_raw if '@' in email_raw else "",
                    "Contact_Person": contact_raw,
                    "Is_Hiring": is_hiring,
                    "Clean_Name": clean,
                    "Active_Jobs_Count": active_count,
                    "Qualifies_Description": f"Approved under {tier_label}. Continuous full-time employees are eligible for TVCS enrollment under Florida Charter School Statute § 1002.33."
                })

            print(f"      ✓ Resolved {resolved_careers_count} direct career and application URLs.")

    except Exception as e:
        print(f"      [!] Error accessing official TVCS API: {e}")

    # Sort: Priority Tier asc, Is_Hiring desc, Active_Jobs desc, Company name asc
    employers.sort(key=lambda x: (x['Priority_Tier'], not x['Is_Hiring'], -x['Active_Jobs_Count'], x['Company']))
    return employers


# ---------------------------------------------------------------------------
# 6. Database Synchronization (SQLite)
# ---------------------------------------------------------------------------
def sync_sqlite_database(unique_jobs, employers_catalog):
    print("\nSynchronizing SQLite Database (tvcs_jobs.db)...")
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Update employers table
        cursor.execute("DROP TABLE IF EXISTS employers")
        cursor.execute("""
            CREATE TABLE employers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employer_id INTEGER,
                company TEXT NOT NULL,
                category TEXT NOT NULL,
                priority_tier INTEGER,
                plaza TEXT,
                address TEXT,
                phone TEXT,
                website TEXT,
                email TEXT,
                contact_person TEXT,
                is_hiring INTEGER,
                active_jobs_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        for emp in employers_catalog:
            cursor.execute("""
                INSERT INTO employers (employer_id, company, category, priority_tier, plaza, address, phone, website, email, contact_person, is_hiring, active_jobs_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                emp.get('Employer_ID', 0), emp['Company'], emp['Category'], emp['Priority_Tier'],
                emp['Plaza'], emp['Address'], emp['Phone'], emp['Website'], emp['Email'],
                emp['Contact_Person'], 1 if emp['Is_Hiring'] else 0, emp['Active_Jobs_Count']
            ))

        # Update job_postings table
        cursor.execute("DROP TABLE IF EXISTS job_postings")
        cursor.execute("""
            CREATE TABLE job_postings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT,
                category TEXT NOT NULL,
                company TEXT NOT NULL,
                job_title TEXT NOT NULL,
                estimated_salary TEXT,
                location TEXT,
                plaza_location TEXT,
                phone TEXT,
                job_link TEXT NOT NULL UNIQUE,
                full_time INTEGER,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        for j in unique_jobs:
            cursor.execute("""
                INSERT OR REPLACE INTO job_postings (source, category, company, job_title, estimated_salary, location, plaza_location, phone, job_link, full_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                j['Source'], j['Category'], j['Company'], j['Job_Title'], j['Estimated_Salary'],
                j['Location'], j['Plaza_Location'], j.get('Phone', ''), j['Job_Link'],
                1 if j['TVCS_Qualifying'] else 0
            ))

        conn.commit()
        conn.close()
        print(f"      ✓ Synced {len(employers_catalog)} employers and {len(unique_jobs)} jobs to {DB_FILE}")
    except Exception as e:
        print(f"      [!] SQLite Sync Error: {e}")


# ---------------------------------------------------------------------------
# Main Execution Pipeline
# ---------------------------------------------------------------------------
async def main():
    print("=" * 75)
    print("TVCS QUALIFYING CAREER & APPROVED BUSINESS HARVEST ENGINE")
    print("=" * 75)

    career_cache = load_career_cache()
    all_jobs = []

    # 1. Harvest TVCS School positions (Category I)
    tvcs_jobs = harvest_tvcs_jobs()
    all_jobs.extend(tvcs_jobs)

    # 2. Harvest The Villages Operating Entities (Category I)
    villages_jobs = harvest_the_villages_operating_jobs()
    all_jobs.extend(villages_jobs)

    # 3. Harvest Sumter County BOCC (Category II)
    sumter_jobs = harvest_sumter_county_jobs()
    all_jobs.extend(sumter_jobs)

    # 3b. Harvest Village Center Community Development District (VCCDD - Category II)
    vccdd_jobs = harvest_vccdd_jobs()
    all_jobs.extend(vccdd_jobs)

    # 4. Harvest Jacobs Engineering (Category II)
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        jacobs_jobs = await harvest_jacobs_jobs(browser)
        all_jobs.extend(jacobs_jobs)
        await browser.close()

    # 5. Harvest 4 Rivers Smokehouse Active Positions (Workstream ATS - Category III)
    four_rivers_jobs = harvest_four_rivers_jobs()
    all_jobs.extend(four_rivers_jobs)

    # Deduplicate verified jobs
    unique_jobs = []
    seen = set()
    for j in all_jobs:
        sig = (j['Job_Title'].strip().lower(), j['Company'].strip().lower())
        if sig not in seen:
            seen.add(sig)
            unique_jobs.append(j)

    # Sort jobs by Priority Tier, Full-Time first, then Title
    unique_jobs.sort(key=lambda x: (x['Priority_Tier'], not x['TVCS_Qualifying'], x['Job_Title']))

    # Write jobs_data.json
    with open(JOBS_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(unique_jobs, f, indent=2)
    print(f"\n[✓] Saved {len(unique_jobs)} VERIFIED active jobs to '{JOBS_OUTPUT_FILE}'")

    # Build and write employers_data.json from official TVCS database
    employers_catalog = harvest_official_tvcs_marketplace(unique_jobs, career_cache)
    with open(EMPLOYERS_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(employers_catalog, f, indent=2)
    print(f"[✓] Saved {len(employers_catalog)} approved employers to '{EMPLOYERS_OUTPUT_FILE}'")

    # Save career cache back to disk
    save_career_cache(career_cache)

    # Update SQLite database
    sync_sqlite_database(unique_jobs, employers_catalog)

    print("\n" + "=" * 75)
    print(f"HARVEST SUCCESS: {len(unique_jobs)} Verified Active Jobs | {len(employers_catalog)} Approved Employers")
    print("=" * 75)


if __name__ == '__main__':
    asyncio.run(main())
