import asyncio
import os
import re
import urllib.parse
import pandas as pd
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

TVCS_DIRECTORY_URL = "https://www.tvcs.org/admission/qualifying-businesses/"
LOCATION = "The Villages, FL"
SEARCH_RADIUS_MILES = "25"
MIN_ANNUAL_SALARY = 100000
MAX_CONCURRENT_PAGES = 3
BATCH_SIZE = 5

ROLE_KEYWORDS = [
    "network", "software", "project manager", "customer service",
    "systems", "infrastructure", "devops", "cloud", "technical support",
    "solutions architect", "engineer", "administrator", "coordinator", "manager"
]

CATEGORY_1_DIRECT_PORTALS = [
    {
        "name": "The Villages Technology Solutions Group",
        "url": "https://www.thevillages.com/careers/search/jsf/jet-engine:career-listing/meta/cat:23/",
        "category": "CATEGORY I"
    },
    {
        "name": "Properties of The Villages / Commercial",
        "url": "https://www.thevillages.com/careers/search/jsf/jet-engine:career-listing/meta/cat:8/",
        "category": "CATEGORY I"
    }
]

def clean_company_name(raw_name):
    name = re.sub(r"(?i)\b(inc|llc|corp|ltd|co|group|dba|pa|pllc)\b\.?", "", raw_name)
    return name.split("/")[0].split("-")[0].strip()

def parse_salary(salary_str):
    if not salary_str:
        return None
    clean = salary_str.replace(",", "").lower()
    if "hour" in clean or "hr" in clean:
        matches = [float(v) for v in re.findall(r"\$?(\d+(?:\.\d+)?)", clean)]
        if matches:
            return max(matches) * 2080
    annual = [float(v) for v in re.findall(r"\$?(\d{4,7})", clean)]
    return max(annual) if annual else None

def extract_businesses_from_html(html, current_category_label):
    soup = BeautifulSoup(html, "html.parser")
    entries = []
    text_content = soup.get_text(separator="\n")
    chunks = re.split(r"(?=\n[^\n]+\nCategory\s+(?:I{1,3}|IV))", text_content)

    for chunk in chunks:
        lines = [l.strip() for l in chunk.split("\n") if l.strip()]
        if not lines:
            continue
        cat_match = re.search(r"Category\s+(I{1,3}|IV)", chunk, re.IGNORECASE)
        cat_tag = cat_match.group(0).upper() if cat_match else f"CATEGORY {current_category_label}"
        raw_company = lines[0]
        company = re.sub(r"(?i)now hiring|hiring only", "", raw_company).strip()

        if company and len(company) < 80:
            entries.append({
                "Company": company,
                "Clean_Name": clean_company_name(company),
                "Category": cat_tag
            })
    return entries

async def block_media(route):
    if route.request.resource_type in ["image", "media", "font", "stylesheet"]:
        await route.abort()
    else:
        await route.continue_()

async def scrape_all_tvcs_categories(page):
    print(f"[1/3] Loading TVCS Marketplace Directory...")
    await page.goto(TVCS_DIRECTORY_URL, wait_until="domcontentloaded", timeout=45000)
    await page.wait_for_timeout(2500)
    all_employers = []

    for cat in ["I", "II", "III", "IV"]:
        print(f"      Scanning Category {cat}...")
        cat_btn = page.locator(f"button.filter-button:has-text('{cat}'), button:text-is('{cat}')")
        if await cat_btn.count() > 0:
            await cat_btn.first.click()
            await page.wait_for_timeout(1500)
        else:
            continue

        current_page = 1
        cat_employers = []
        while True:
            html = await page.content()
            new_entries = extract_businesses_from_html(html, cat)
            existing_names = {e["Company"] for e in cat_employers}
            for entry in new_entries:
                if entry["Company"] not in existing_names:
                    cat_employers.append(entry)
                    existing_names.add(entry["Company"])

            next_target = current_page + 1
            page_btn = page.locator(f".mp-page-number:has-text('{next_target}'), div.mp-page-number:text-is('{next_target}')")
            if await page_btn.count() > 0 and await page_btn.first.is_visible():
                await page_btn.first.click(force=True)
                current_page += 1
                await page.wait_for_timeout(1200)
            else:
                break
        all_employers.extend(cat_employers)

    df = pd.DataFrame(all_employers).drop_duplicates(subset=["Company"])
    print(f"[✓] Extracted {len(df)} total employers across Categories I–IV.")
    return df

async def scrape_direct_portals(page):
    print("\n[2/3] Checking Direct Category 1 Villages Portals...")
    direct_matches = []
    for portal in CATEGORY_1_DIRECT_PORTALS:
        try:
            await page.goto(portal["url"], wait_until="domcontentloaded", timeout=25000)
            await page.wait_for_timeout(2000)
            soup = BeautifulSoup(await page.content(), "html.parser")
            cards = soup.select(".jet-listing-grid__item, .elementor-post, article")
            for card in cards:
                text = card.get_text(separator=" ").strip()
                title_el = card.select_one("h2, h3, .jet-listing-dynamic-field__content")
                title = title_el.get_text().strip() if title_el else "Tech Role"
                link_el = card.select_one("a[href*='/careers/']")
                job_link = link_el["href"] if link_el and link_el.has_attr("href") else portal["url"]

                if any(kw in text.lower() for kw in ROLE_KEYWORDS):
                    direct_matches.append({
                        "Source": "Direct ATS",
                        "Category": portal["category"],
                        "Company": portal["name"],
                        "Job_Title": title,
                        "Estimated_Salary": "Unlisted (Enterprise Scale)",
                        "Location": "The Villages, FL",
                        "Job_Link": job_link
                    })
                    print(f"      ✓ Direct Match: {title} @ {portal['name']}")
        except Exception:
            pass
    return direct_matches

async def search_google_jobs_batch(context, batch_items, sem):
    async with sem:
        page = await context.new_page()
        await page.route("**/*", block_media)
        company_subquery = " OR ".join([f'"{item["Clean_Name"]}"' for item in batch_items if item["Clean_Name"]])
        roles_subquery = '("network" OR "software" OR "project manager" OR "customer service" OR "systems" OR "engineer")'
        query = f'({company_subquery}) {roles_subquery} "The Villages, FL"'
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&ibp=htl;jobs"

        matches = []
        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(1500)
            soup = BeautifulSoup(await page.content(), "html.parser")
            job_cards = soup.select("li.PUpOsf, div.gws-plugins-horizon-jobs__li-ed, div.s3tdad")

            for card in job_cards:
                title_el = card.select_one("div.BjJfJf, .KLsYvd, div[role='heading']")
                job_title = title_el.get_text().strip() if title_el else ""
                comp_el = card.select_one("div.vNEEBe, .nJlQNd")
                comp_name = comp_el.get_text().strip() if comp_el else "Qualifying Business"
                snippet_el = card.select_one("div.HBtIp, div.I2Cbhb")
                snippet = snippet_el.get_text(separator=" ").strip() if snippet_el else ""

                if any(kw in f"{job_title} {snippet}".lower() for kw in ROLE_KEYWORDS):
                    matched_category = "Qualifying Tier"
                    for item in batch_items:
                        if item["Clean_Name"].lower() in comp_name.lower():
                            matched_category = item["Category"]
                            break
                    matches.append({
                        "Source": "Google Jobs / Direct ATS",
                        "Category": matched_category,
                        "Company": comp_name,
                        "Job_Title": job_title,
                        "Estimated_Salary": "Check ATS Posting",
                        "Location": "The Villages / Sumter County, FL",
                        "Job_Link": search_url
                    })
                    print(f"      ✓ Aggregator Match: {job_title} @ {comp_name} ({matched_category})")
        except Exception:
            pass
        finally:
            await page.close()
        return matches

async def main():
    stealth = Stealth()
    all_results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled", "--no-sandbox"])
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

        # 1. TVCS Directory
        dir_page = await context.new_page()
        await stealth.apply_stealth_async(dir_page)
        df_employers = await scrape_all_tvcs_categories(dir_page)
        await dir_page.close()

        # 2. Direct Category 1 Portals
        direct_page = await context.new_page()
        await stealth.apply_stealth_async(direct_page)
        direct_jobs = await scrape_direct_portals(direct_page)
        all_results.extend(direct_jobs)
        await direct_page.close()

        # 3. Aggregated Search Batches
        print("\n[3/3] Scanning ATS & Aggregators for extracted businesses...")
        employers = df_employers.to_dict("records")
        batches = [employers[i:i + BATCH_SIZE] for i in range(0, len(employers), BATCH_SIZE)]
        sem = asyncio.Semaphore(MAX_CONCURRENT_PAGES)
        tasks = [search_google_jobs_batch(context, b, sem) for b in batches]
        nested = await asyncio.gather(*tasks)
        for sub in nested:
            all_results.extend(sub)

        await browser.close()

    # 4. Final Export
    if all_results:
        df = pd.DataFrame(all_results).drop_duplicates(subset=["Job_Title", "Company"])
        df.to_json("jobs_data.json", orient="records", indent=2)
        df.to_csv("all_categories_all_sources_jobs.csv", index=False)
        print(f"\n[✓] Finished. Exported {len(df)} opportunities to 'jobs_data.json' and CSV.")
    else:
        print("\nNo matching positions found in this run.")

if __name__ == "__main__":
    asyncio.run(main())