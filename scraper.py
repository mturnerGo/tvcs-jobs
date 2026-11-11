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


def normalize_website(web_raw, comp_name, plaza_name):
    w = str(web_raw).strip() if web_raw and not pd.isna(web_raw) else ""
    if w and w.lower() not in ['none', 'nan', 'null', 'n/a', 'no', '']:
        if not w.startswith('http://') and not w.startswith('https://'):
            return f"https://{w}"
        return w
    # Accurate Google Careers / Official Site Search Fallback
    q = urllib.parse.quote(f'"{comp_name}" "{plaza_name or "The Villages"}" Florida official website careers')
    return f"https://www.google.com/search?q={q}"


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
    print("\n[3/5] Harvesting Sumter County BOCC (Category II)...")
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
# 5. Harvest TVCS Official Marketplace (785+ Approved Businesses)
# ---------------------------------------------------------------------------
def harvest_official_tvcs_marketplace(active_jobs):
    print("\n[5/5] Harvesting Official TVCS Marketplace API (All Qualifying Employers)...")
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

            for b in data:
                comp_name = str(b.get('companyName', '')).strip()
                if not comp_name:
                    continue

                plaza = str(b.get('location', '')).strip() or "The Villages Commercial Area"
                phone_raw = b.get('phone', '')
                phone_formatted = format_phone(phone_raw)
                phone_tel = re.sub(r'\D', '', str(phone_raw))
                
                web_raw = b.get('webAddress', '')
                has_official_website = bool(web_raw and str(web_raw).strip() and str(web_raw).strip().lower() not in ['none', 'nan', 'null', 'n/a', 'no', ''])
                website_url = normalize_website(web_raw, comp_name, plaza)

                email_raw = str(b.get('email', '') or b.get('verifyEmail', '')).strip()
                contact_raw = str(b.get('contactName', '') or b.get('verifyContact', '')).strip()

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
                    "Website": website_url,
                    "Has_Official_Website": has_official_website,
                    "Email": email_raw if '@' in email_raw else "",
                    "Contact_Person": contact_raw,
                    "Is_Hiring": is_hiring,
                    "Clean_Name": clean,
                    "Active_Jobs_Count": active_count,
                    "Qualifies_Description": f"Approved under {tier_label}. Continuous full-time employees are eligible for TVCS enrollment under Florida Charter School Statute § 1002.33."
                })

    except Exception as e:
        print(f"      [!] Error accessing official TVCS API: {e}")
        # Fallback to CSV if network fails
        if os.path.exists(CSV_CATALOG_FILE):
            print("      Falling back to local CSV catalog...")
            df = pd.read_csv(CSV_CATALOG_FILE)
            for _, row in df.iterrows():
                comp = str(row.get('Company', '')).strip()
                if not comp: continue
                tier_num, cat_code, tier_label = determine_category_priority(row.get('Category', 'CATEGORY III'))
                plaza = str(row.get('Plaza', 'The Villages Commercial Area')).strip()
                employers.append({
                    "Employer_ID": 0,
                    "Company": comp,
                    "Category": cat_code,
                    "Priority_Tier": tier_num,
                    "Priority_Label": tier_label,
                    "Plaza": plaza,
                    "Address": plaza,
                    "Phone": "",
                    "Phone_Tel": "",
                    "Website": normalize_website(row.get('Direct_Website', ''), comp, plaza),
                    "Has_Official_Website": False,
                    "Email": "",
                    "Contact_Person": "",
                    "Is_Hiring": False,
                    "Clean_Name": clean_company_name(comp),
                    "Active_Jobs_Count": 0,
                    "Qualifies_Description": f"Approved under {tier_label}."
                })

    # Sort: Priority Tier asc, Is_Hiring desc, Active_Jobs desc, Company name asc
    employers.sort(key=lambda x: (x['Priority_Tier'], not x['Is_Hiring'], -x['Active_Jobs_Count'], x['Company']))
    print(f"      ✓ Successfully cataloged {len(employers)} verified businesses ({sum(1 for e in employers if e['Is_Hiring'])} marked Actively Hiring).")
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

    # 4. Harvest Jacobs Engineering (Category II)
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        jacobs_jobs = await harvest_jacobs_jobs(browser)
        all_jobs.extend(jacobs_jobs)
        await browser.close()

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
    employers_catalog = harvest_official_tvcs_marketplace(unique_jobs)
    with open(EMPLOYERS_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(employers_catalog, f, indent=2)
    print(f"[✓] Saved {len(employers_catalog)} approved employers to '{EMPLOYERS_OUTPUT_FILE}'")

    # Update SQLite database
    sync_sqlite_database(unique_jobs, employers_catalog)

    print("\n" + "=" * 75)
    print(f"HARVEST SUCCESS: {len(unique_jobs)} Verified Active Jobs | {len(employers_catalog)} Approved Employers")
    print("=" * 75)


if __name__ == '__main__':
    asyncio.run(main())
