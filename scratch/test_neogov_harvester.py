import urllib.request
import ssl
from bs4 import BeautifulSoup
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'X-Requested-With': 'XMLHttpRequest'
}

def harvest_neogov_agency(agency_id, company_name, category="CATEGORY II", priority_tier=2, priority_label="Category II (Government/Service Partner - 2nd Priority)"):
    print(f"\nHarvesting NeoGov agency: {agency_id} ({company_name})...")
    url = f"https://www.governmentjobs.com/careers/home/index?agency={agency_id}&sort=PositionTitle&isDescendingSort=false"
    jobs = []
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            rows = soup.select('li.list-item, tr.job-table-row')
            
            seen_ids = set()
            for r in rows:
                link_el = r.select_one('a.item-details-link, a.job-details-link, a[href*="/jobs/"]')
                if not link_el:
                    continue
                href = link_el.get('href', '')
                title = link_el.text.strip()
                if not title or not href or href in seen_ids:
                    continue
                seen_ids.add(href)
                
                full_url = f"https://www.governmentjobs.com{href}" if href.startswith('/') else href
                
                # Check text for job type & salary
                row_text = " ".join(r.stripped_strings)
                t_lower = (title + " " + row_text).lower()
                
                full_time = True
                if 'part time' in t_lower or 'part-time' in t_lower or 'adjunct' in t_lower or 'student assistant' in t_lower or 'temporary' in t_lower:
                    full_time = False
                elif 'full time' in t_lower or 'full-time' in t_lower:
                    full_time = True
                    
                # Salary extraction
                salary_m = re.search(r'(\$[\d,.]+\s*(?:-\s*\$[\d,.]+)?\s*(?:Hourly|Annually|Monthly))', row_text, re.I)
                salary = salary_m.group(1) if salary_m else "Official Municipal / State Scale"
                
                # Department
                dept_m = re.search(r'Department:\s*([^|]+)', row_text)
                dept = dept_m.group(1).strip() if dept_m else ""
                
                plaza = f"{company_name} Facilities"
                if dept:
                    plaza = f"{company_name} - {dept}"
                    
                # Phone
                phone = "(352) 330-1340" if agency_id == 'wildwoodfl' else ("(352) 365-3557" if agency_id == 'lsscedu' else "(352) 689-4400")
                
                jobs.append({
                    "Job_Title": f"{company_name} - {title}",
                    "Company": company_name,
                    "Category": category,
                    "Priority_Tier": priority_tier,
                    "Priority_Label": priority_label,
                    "Employment_Type": "Full-Time" if full_time else "Part-Time",
                    "TVCS_Qualifying": full_time,
                    "Plaza_Location": plaza,
                    "Location": "Wildwood / The Villages / Sumter County, FL",
                    "Phone": phone,
                    "Estimated_Salary": salary,
                    "Source": f"{company_name} (Official NeoGov ATS)",
                    "Job_Link": full_url,
                    "Posted_Date": "Recent",
                    "Description": f"Public sector position with {company_name}. {'Full-time continuous employment qualifies for Category II TVCS enrollment priority under Florida Statute § 1002.33.' if full_time else 'Part-time / seasonal position.'}"
                })
        print(f"      ✓ {company_name}: Captured {len(jobs)} active positions.")
    except Exception as e:
        print(f"      [!] Error harvesting {agency_id}: {e}")
    return jobs

for ag, comp in [('wildwoodfl', 'City of Wildwood'), ('lsscedu', 'Lake-Sumter State College'), ('sumtercountyfl', 'Sumter County BOCC')]:
    res = harvest_neogov_agency(ag, comp)
    for j in res[:2]:
        print("  -", j['Job_Title'], "|", j['Employment_Type'], "|", j['Estimated_Salary'], "|", j['Job_Link'])
