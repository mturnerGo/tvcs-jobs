"""
Universal Autonomous Job Harvester
----------------------------------
Automated job discovery and extraction for TVCS certified employers.
Inspired by modern job aggregators (e.g. HiringCafe, Google Jobs):
- Discovers careers pages automatically from official company URLs.
- Identifies underlying ATS protocols (Workday, Greenhouse, ADP, Paylocity, ClearCompany, etc.).
- Extracts Schema.org JobPosting structured JSON-LD.
- Normalizes and geofences positions to The Villages, FL and surrounding qualified municipalities.
- Maps discovered jobs directly to certified TVCS Category (I-IV) rules.
"""

import sys
import os
import json
import re
import ssl
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

from engine.drivers import (
    driver_greenhouse,
    driver_paylocity,
    driver_schema_org,
    driver_workday_cxs,
    driver_adp_wfn,
    driver_icims_jibe,
    driver_clearcompany_api,
    driver_ultipro_board
)
from engine.whitelist_matcher import WhitelistMatcher

matcher = WhitelistMatcher()

SSL_CTX = ssl._create_unverified_context()
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

VILLAGES_GEOFENCE = [
    'the villages', 'villages', 'wildwood', 'lady lake', 'fruitland park',
    'sumterville', 'oxford', 'belleview', 'leesburg', 'sumter', 'lake county',
    'middleton', 'eastport', 'brownwood', 'lake sumter', 'spanish springs',
    '32162', '32163', '32159', '34785', '34491'
]

def is_villages_geofenced(text):
    if not text:
        return False
    t = text.lower()
    return any(loc in t for loc in VILLAGES_GEOFENCE)

def sniff_and_harvest_company(company_name, company_url):
    """
    Takes any company name and URL and attempts autonomous discovery:
    1. Schema.org JobPosting JSON-LD
    2. Greenhouse
    3. Paylocity
    4. Workday
    5. ADP Workforce Now
    6. Dedicated Career Page extraction
    """
    if not company_url or 'google.com' in company_url:
        return []

    try:
        req = urllib.request.Request(company_url, headers=DEFAULT_HEADERS)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=8) as resp:
            final_url = resp.geturl()
            html = resp.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')

            # Protocol 1: Check for Greenhouse
            gh_m = re.search(r'boards\.greenhouse\.io/([a-zA-Z0-9_\-]+)', html)
            if gh_m:
                board = gh_m.group(1)
                feed = {'company': company_name, 'board': board, 'filter_locations': VILLAGES_GEOFENCE}
                jobs = driver_greenhouse(feed)
                if jobs:
                    return jobs

            # Protocol 2: Check for Paylocity
            pay_m = re.search(r'https?://recruiting\.paylocity\.com/recruiting/jobs/All/[^\s"\'<>]+', html)
            if pay_m:
                pay_url = pay_m.group(0).split('?')[0]
                feed = {'company': company_name, 'url': pay_url, 'filter_locations': VILLAGES_GEOFENCE}
                jobs = driver_paylocity(feed)
                if jobs:
                    return jobs
            elif 'recruiting.paylocity.com' in final_url:
                feed = {'company': company_name, 'url': final_url, 'filter_locations': VILLAGES_GEOFENCE}
                jobs = driver_paylocity(feed)
                if jobs:
                    return jobs

            # Protocol 3: Check for Workday
            wd_m = re.search(r'https?://([a-zA-Z0-9_\-\.]+)\.myworkdayjobs\.com/([a-zA-Z0-9_\-]+)', html)
            if wd_m:
                tenant = wd_m.group(1)
                site = wd_m.group(2)
                base_cxs = f"https://{tenant}.myworkdayjobs.com/wday/cxs/{tenant.split('.')[0]}/{site}"
                feed = {'company': company_name, 'base_url': base_cxs, 'search_queries': ['Villages', 'Wildwood', 'Lady Lake']}
                jobs = driver_workday_cxs(feed)
                if jobs:
                    return jobs

            # Protocol 4: Check for Schema.org JobPosting
            feed = {'company': company_name, 'url': final_url, 'filter_locations': VILLAGES_GEOFENCE}
            jobs = driver_schema_org(feed)
            if jobs:
                return jobs

            # Protocol 5: Check if there is an unvisited /careers link
            if 'career' not in final_url.lower() and 'job' not in final_url.lower():
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    t = a.get_text(strip=True).lower()
                    hl = href.lower()
                    if any(k in t for k in ['career', 'join our team', 'work with us', 'current openings']) or any(k in hl for k in ['/careers', '/jobs']):
                        career_target = urllib.parse.urljoin(final_url, href)
                        if career_target != final_url:
                            # Recurse one level on career target
                            return sniff_and_harvest_company(company_name, career_target)

    except Exception as e:
        pass

    return []

def harvest_discovered_endpoints():
    """
    Harvests all endpoints saved in discovered_company_endpoints.json
    """
    endpoints_file = 'discovered_company_endpoints.json'
    if not os.path.exists(endpoints_file):
        print("No discovered_company_endpoints.json found. Run scanner first.")
        return []

    with open(endpoints_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    all_harvested = []
    
    # Process ATS endpoints
    ats_items = data.get('ats_detected', [])
    print(f"Harvesting {len(ats_items)} discovered ATS endpoints...")
    for item in ats_items:
        co = item['company']
        ats = item['ats']
        url = item['url']
        
        jobs = []
        if ats == 'greenhouse':
            m = re.search(r'boards\.greenhouse\.io/([a-zA-Z0-9_\-]+)', url)
            if m:
                jobs = driver_greenhouse({'company': co, 'board': m.group(1), 'filter_locations': VILLAGES_GEOFENCE})
        elif ats == 'paylocity':
            jobs = driver_paylocity({'company': co, 'url': url, 'filter_locations': VILLAGES_GEOFENCE})
        
        for j in jobs:
            match_info = matcher.match(co)
            j['Company'] = match_info['canonical_company']
            j['Category'] = match_info['Category']
            j['Priority_Tier'] = match_info['Priority_Tier']
            all_harvested.append(j)

    print(f"Total jobs harvested from autonomous endpoints: {len(all_harvested)}")
    return all_harvested

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Universal Autonomous Job Harvester")
    parser.add_argument('--company', type=str, help="Company name to harvest")
    parser.add_argument('--url', type=str, help="Company URL to analyze")
    parser.add_argument('--harvest-all', action='store_true', help="Harvest all discovered endpoints")
    args = parser.parse_args()

    if args.company and args.url:
        print(f"Autonomous harvesting for: {args.company} ({args.url})")
        jobs = sniff_and_harvest_company(args.company, args.url)
        print(f"Found {len(jobs)} active jobs:")
        for j in jobs:
            print(" -", j['Job_Title'], "|", j['Location'], "|", j['Job_Link'])
    elif args.harvest_all:
        harvest_discovered_endpoints()
    else:
        print("Usage: python -m engine.universal_harvester --company 'Name' --url 'https://...' OR --harvest-all")
