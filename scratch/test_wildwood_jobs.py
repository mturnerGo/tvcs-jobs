from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://www.governmentjobs.com/careers/wildwoodfl', timeout=20000)
    time.sleep(4)
    links = page.query_selector_all('a[href*="/jobs/"]')
    seen = set()
    print('Wildwood Jobs:')
    for l in links:
        title = l.inner_text().strip()
        href = l.get_attribute('href')
        if title and href and href not in seen:
            seen.add(href)
            print(f"  * {title} => https://www.governmentjobs.com{href}")
    browser.close()
