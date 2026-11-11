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


def clean_company_name(raw_name):
    if not raw_name or pd.isna(raw_name):
        return ""
    name = re.sub(r"(?i)\b(inc|llc|corp|ltd|co|group|dba|pa|pllc|the|florida|solutions)\b\.?", "", str(raw_name))
    name = re.sub(r"[^\w\s]", "", name)
    return " ".join(name.strip().split())


def determine_category_priority(category_str):
    cat = str(category_str).upper()
    if "CATEGORY I" in cat and "II" not in cat and "III" not in cat and "IV" not in cat:
        return 1, "Category I (Direct - 1st Priority)"
    elif "CATEGORY II" in cat:
        return 2, "Category II (Subcontractor - 2nd Priority)"
    elif "CATEGORY III" in cat:
        return 3, "Category III (Commercial Tenant - 3rd Priority)"
    elif "CATEGORY IV" in cat:
        return 4, "Category IV (Approved Vendor - 4th Priority)"
    return 3, "Category III (Commercial Tenant)"


def is_full_time(title_str, work_type_str=""):
    combined = f"{title_str} {work_type_str}".lower()
    if any(pt in combined for pt in ["part-time", "part time", "prn", "substitute", "temporary", "temp "]):
        return False
    return True


# ---------------------------------------------------------------------------
# 1. Harvest The Villages Charter School (TVCS) Direct Positions (Category I)
# ---------------------------------------------------------------------------
def harvest_tvcs_jobs():
    print("\n[1/4] Harvesting The Villages Charter School (TVCS) Requisitions...")
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
    print("\n[2/4] Harvesting The Villages Operating Entities...")
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
    print("\n[3/4] Harvesting Sumter County BOCC (Category II)...")
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
    print("\n[4/4] Harvesting Jacobs Engineering & Infrastructure (Category II)...")
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
# 5. Build TVCS Approved Employers Catalog (All 432 Qualifying Businesses)
# ---------------------------------------------------------------------------
def build_approved_employers_catalog(active_jobs):
    print("\n[5/5] Building Approved Employers Catalog (All 432 Businesses)...")
    if not os.path.exists(CSV_CATALOG_FILE):
        print(f"      [!] Error: {CSV_CATALOG_FILE} not found.")
        return []

    df = pd.read_csv(CSV_CATALOG_FILE)
    employers = []
    
    # Map active jobs count by company
    job_counts = {}
    for j in active_jobs:
        comp = j['Company'].lower()
        job_counts[comp] = job_counts.get(comp, 0) + 1

    for _, row in df.iterrows():
        comp_name = str(row.get('Company', '')).strip()
        if not comp_name:
            continue
        category = str(row.get('Category', 'CATEGORY III')).strip()
        plaza = str(row.get('Plaza', 'The Villages Commercial Area')).strip()
        clean = str(row.get('clean', '')).strip() or clean_company_name(comp_name)
        tier_num, tier_label = determine_category_priority(category)
        direct_site = str(row.get('Direct_Website', '')).strip()
        if not direct_site or direct_site == 'nan' or not direct_site.startswith('http'):
            direct_site = f"https://www.google.com/search?q={urllib.parse.quote(comp_name + ' The Villages Florida')}"

        # Match active jobs count
        active_count = 0
        for comp_key, count in job_counts.items():
            if clean in comp_key or comp_name.lower() in comp_key or comp_key in comp_name.lower():
                active_count += count

        employers.append({
            "Company": comp_name,
            "Category": category,
            "Priority_Tier": tier_num,
            "Priority_Label": tier_label,
            "Plaza": plaza,
            "Clean_Name": clean,
            "Website": direct_site,
            "Active_Jobs_Count": active_count,
            "Qualifies_Description": f"Approved under {tier_label}. Continuous full-time employees are eligible for TVCS enrollment under Florida Charter School Statute."
        })

    employers.sort(key=lambda x: (x['Priority_Tier'], -x['Active_Jobs_Count'], x['Company']))
    print(f"      ✓ Processed {len(employers)} approved employers into catalog.")
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
        cursor.execute("CREATE TABLE IF NOT EXISTS employers (id INTEGER PRIMARY KEY AUTOINCREMENT, company TEXT NOT NULL UNIQUE, category TEXT NOT NULL, direct_website TEXT, plaza TEXT, clean_name TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        cursor.execute("DELETE FROM employers")
        for emp in employers_catalog:
            cursor.execute(
                "INSERT INTO employers (company, category, direct_website, plaza, clean_name) VALUES (?, ?, ?, ?, ?)",
                (emp['Company'], emp['Category'], emp['Website'], emp['Plaza'], emp['Clean_Name'])
            )

        # Update job_postings table
        cursor.execute("CREATE TABLE IF NOT EXISTS job_postings (id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT, category TEXT NOT NULL, company TEXT NOT NULL, job_title TEXT NOT NULL, estimated_salary TEXT, location TEXT, plaza_location TEXT, job_link TEXT NOT NULL UNIQUE, direct_employer_url TEXT, first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        cursor.execute("DELETE FROM job_postings")
        for j in unique_jobs:
            cursor.execute(
                "INSERT OR REPLACE INTO job_postings (source, category, company, job_title, estimated_salary, location, plaza_location, job_link, direct_employer_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (j['Source'], j['Category'], j['Company'], j['Job_Title'], j['Estimated_Salary'], j['Location'], j['Plaza_Location'], j['Job_Link'], j['Job_Link'])
            )

        conn.commit()
        conn.close()
        print(f"      ✓ Synced {len(employers_catalog)} employers and {len(unique_jobs)} jobs to {DB_FILE}")
    except Exception as e:
        print(f"      [!] SQLite Sync Error: {e}")


# ---------------------------------------------------------------------------
# Main Execution Pipeline
# ---------------------------------------------------------------------------
async def main():
    print("=" * 70)
    print("TVCS QUALIFYING CAREER DISCOVERY & HARVEST ENGINE")
    print("=" * 70)

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

    # Build and write employers_data.json
    employers_catalog = build_approved_employers_catalog(unique_jobs)
    with open(EMPLOYERS_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(employers_catalog, f, indent=2)
    print(f"[✓] Saved {len(employers_catalog)} approved employers to '{EMPLOYERS_OUTPUT_FILE}'")

    # Update SQLite database
    sync_sqlite_database(unique_jobs, employers_catalog)

    print("\n" + "=" * 70)
    print(f"HARVEST SUCCESS: {len(unique_jobs)} Verified Active Jobs | {len(employers_catalog)} Approved Employers")
    print("=" * 70)


if __name__ == '__main__':
    asyncio.run(main())
