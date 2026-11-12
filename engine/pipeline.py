"""
TVCS Scalable Master Pipeline
-----------------------------
Executes all declarative feeds from company_feeds.json and autonomous
crawlers, enriches every job with WhitelistMatcher, deduplicates,
and syncs to jobs_data.json and tvcs_jobs.db.
"""

import json
import sqlite3
import argparse
import concurrent.futures
import os
import sys

# Ensure root directory is on python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from engine.drivers import execute_driver
from engine.whitelist_matcher import WhitelistMatcher

def run_pipeline(dry_run=False):
    print("=" * 70)
    print("  TVCS UNIFIED JOB INGESTION PIPELINE")
    print(f"  Mode: {'DRY RUN (Validation Only)' if dry_run else 'PRODUCTION SYNC'}")
    print("=" * 70)

    # 1. Load feeds configuration
    with open('engine/company_feeds.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    feeds = config.get('feeds', [])
    print(f"[*] Loaded {len(feeds)} declarative company feeds from company_feeds.json")

    # 2. Initialize Whitelist Matcher
    matcher = WhitelistMatcher('employers_data.json')
    print(f"[*] Whitelist Matcher initialized with {len(matcher.exact_map)} certified employers")

    # 3. Execute declarative feeds concurrently
    raw_jobs = []
    feed_counts = {}

    print("\n[*] Ingesting declarative ATS feeds...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_feed = {executor.submit(execute_driver, f): f for f in feeds}
        for future in concurrent.futures.as_completed(future_to_feed):
            feed = future_to_feed[future]
            feed_id = feed['id']
            company = feed['company']
            try:
                jobs = future.result()
                raw_jobs.extend(jobs)
                feed_counts[company] = len(jobs)
                print(f"  [+] {company}: {len(jobs)} jobs")
            except Exception as e:
                print(f"  [!] Failed {company} ({feed_id}): {e}")

    # 4. Also ingest autonomous crawler jobs if present in current jobs_data.json
    try:
        with open('jobs_data.json', 'r', encoding='utf-8') as f:
            existing = json.load(f)
            # Add existing jobs not from declarative feeds (e.g. Florida Cancer Specialists, United Health)
            existing_companies = set(f['company'] for f in feeds)
            for j in existing:
                if j.get('Company') not in existing_companies:
                    raw_jobs.append(j)
    except Exception as e:
        print(f"Note: existing jobs read error: {e}")

    print(f"\n[*] Total raw jobs collected: {len(raw_jobs)}")

    # 5. Enrich with Whitelist Matcher & Deduplicate
    enriched_jobs = []
    seen_links = set()
    seen_keys = set()

    for job in raw_jobs:
        title = job.get('Job_Title', '').strip()
        comp = job.get('Company', '').strip()
        link = job.get('Job_Link', '').strip()
        if not title or not link:
            continue

        key = f"{title.lower()}___{comp.lower()}"
        if link in seen_links or key in seen_keys:
            continue

        seen_links.add(link)
        seen_keys.add(key)

        # Match with whitelist
        match_info = matcher.match(comp)
        
        enriched_jobs.append({
            "Job_Title": title,
            "Company": match_info['canonical_company'],
            "Estimated_Salary": job.get('Estimated_Salary', 'Competitive'),
            "Location": job.get('Location', 'The Villages, FL'),
            "Plaza_Location": match_info['Plaza_Location'],
            "Phone": match_info['Phone'],
            "Category": match_info['Category'],
            "Priority_Tier": match_info['Priority_Tier'],
            "Priority_Label": match_info['Priority_Label'],
            "Job_Link": link,
            "Description": job.get('Description', f"Active position with {comp}."),
            "Employment_Type": job.get('Employment_Type', 'Full-Time'),
            "TVCS_Qualifying": True
        })

    # Sort: Tier 1 first, then Tier 2, 3, 4, then Company name, then Title
    enriched_jobs.sort(key=lambda x: (x['Priority_Tier'], x['Company'], x['Job_Title']))

    # Print summary breakdown
    category_counts = {}
    for j in enriched_jobs:
        c = j['Category']
        category_counts[c] = category_counts.get(c, 0) + 1

    print("\n" + "=" * 70)
    print("  HARVEST & ENRICHMENT REPORT")
    print("=" * 70)
    print(f"Total Unique Validated Jobs: {len(enriched_jobs)}")
    for cat in ['CATEGORY I', 'CATEGORY II', 'CATEGORY III', 'CATEGORY IV']:
        print(f"  * {cat}: {category_counts.get(cat, 0)} jobs")
    print(f"Total Companies with Active Jobs: {len(set(j['Company'] for j in enriched_jobs))}")

    if dry_run:
        print("\n[DRY RUN] No files were modified. Run without --dry-run to apply to production.")
        return enriched_jobs

    # 6. Apply to production files
    with open('jobs_data.json', 'w', encoding='utf-8') as f:
        json.dump(enriched_jobs, f, indent=2)
    print("\n[✓] Successfully updated 'jobs_data.json'")

    # Sync to SQLite
    conn = sqlite3.connect('tvcs_jobs.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM job_postings WHERE source = 'Unified Pipeline'")
    for j in enriched_jobs:
        cursor.execute('''
            INSERT OR REPLACE INTO job_postings 
            (source, category, company, job_title, estimated_salary, location, plaza_location, phone, job_link, full_time, first_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (
            'Unified Pipeline',
            j['Category'],
            j['Company'],
            j['Job_Title'],
            j['Estimated_Salary'],
            j['Location'],
            j['Plaza_Location'],
            j['Phone'],
            j['Job_Link'],
            1 if j['Employment_Type'] == 'Full-Time' else 0
        ))
    conn.commit()
    conn.close()
    print("[✓] Successfully synchronized 'tvcs_jobs.db'")
    print("=" * 70)

    return enriched_jobs

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="TVCS Scalable Master Pipeline")
    parser.add_argument('--dry-run', action='store_true', help="Validate pipeline without writing to disk")
    args = parser.parse_args()
    run_pipeline(dry_run=args.dry_run)
