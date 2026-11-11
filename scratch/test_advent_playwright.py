from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    try:
        page.goto('https://www.adventhealthcareers.com/search-results?keywords=The%20Villages', timeout=20000)
        time.sleep(4)
        print("Advent Page Title:", page.title())
        links = page.query_selector_all('a[href*="/job/"]')
        print("Advent jobs found:", len(links))
        for l in links[:5]:
            print("  *", l.inner_text().strip(), "=>", l.get_attribute('href'))
    except Exception as e:
        print("Advent error:", e)
    browser.close()
