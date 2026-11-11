from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    api_calls = []
    def log_response(res):
        u = res.url
        if any(k in u for k in ['job', 'search', 'api', 'list', 'graphql', 'content']) and not any(ext in u for ext in ['.css', '.js', '.png', '.svg', '.woff', '.ico']):
            api_calls.append((res.status, u))
                
    page.on('response', log_response)
    
    page.goto('https://www.governmentjobs.com/careers/sumtercountyfl', timeout=30000)
    time.sleep(5)
    
    print("Page title:", page.title())
    print("\nInteresting Network Responses:")
    for status, u in api_calls:
        print(f"  [{status}] {u}")
        
    # Check elements on page
    links = page.query_selector_all('a[href*="/jobs/"]')
    print(f"\nFound {len(links)} job links:")
    for l in links[:15]:
        print("  -", l.inner_text().strip(), "=>", l.get_attribute('href'))
        
    browser.close()
