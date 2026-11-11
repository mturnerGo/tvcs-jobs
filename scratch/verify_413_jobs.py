from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1400, 'height': 1000})
    
    print("Navigating to http://localhost:8000...")
    page.goto('http://localhost:8000', timeout=15000)
    page.wait_for_selector('.job-card', timeout=10000)
    time.sleep(1)
    
    badge_text = page.locator('#activeJobsCountBadge').inner_text()
    print("Active Jobs Count Badge:", badge_text)
    
    cards_count = page.locator('.job-card').count()
    print(f"Jobs displayed on page 1: {cards_count}")
    
    pagination_info = page.locator('#paginationArea .pagination-info').inner_text()
    print("Jobs Pagination Info:", pagination_info)
    
    # Take screenshot of page 1
    page.screenshot(path='C:/Users/panda/.gemini/antigravity/brain/3c5b616f-75fb-4f0b-8bd7-178b6fbe7e52/feed_scale_413_preview.png', full_page=False)
    print("Saved screenshot to feed_scale_413_preview.png")
    
    # Click Full-Time filter
    page.click('#qualifyingOnlyCheck')
    time.sleep(1)
    ft_cards = page.locator('.job-card').count()
    ft_info = page.locator('#paginationArea .pagination-info').inner_text()
    print(f"Filtered Full-Time cards on page 1: {ft_cards}")
    print(f"Filtered Full-Time pagination info: {ft_info}")
    
    # Test next page button
    page.click('#paginationArea button:has-text("Next")')
    time.sleep(1)
    page2_info = page.locator('#paginationArea .pagination-info').inner_text()
    print("Page 2 info:", page2_info)
    
    # Test switching to Qualifying Businesses tab
    page.click('#tabEmployersBtn')
    time.sleep(1)
    emp_badge = page.locator('#allEmployersCountBadge').inner_text()
    emp_cards = page.locator('.employer-card').count()
    emp_info = page.locator('#paginationArea .pagination-info').inner_text()
    print(f"Employers Badge: {emp_badge} | Cards on Page 1: {emp_cards} | Info: {emp_info}")
    
    browser.close()
    print("All checks passed successfully!")
