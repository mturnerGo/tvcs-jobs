from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('http://localhost:8000/scratch/test_resume_matcher.html')
    res = page.evaluate('() => window.results')
    for r in res:
        print(f"{r['Job_Title']}: {r['matchScore']}% | Matched: {r['matchedSkills']}")
    browser.close()
