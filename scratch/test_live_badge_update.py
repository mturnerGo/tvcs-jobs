from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1400, 'height': 900})
    
    print("Navigating to http://localhost:8000...")
    page.goto('http://localhost:8000', timeout=15000)
    page.wait_for_selector('.job-card', timeout=10000)
    time.sleep(1)
    
    # 1. Initial State
    initial_badge = page.locator('#activeJobsCountBadge').inner_text()
    print(f"1. Initial Active Jobs Badge: {initial_badge}")
    assert initial_badge == "413", f"Expected 413, got {initial_badge}"
    
    # 2. Search "Wildwood"
    page.fill('#searchInput', 'Wildwood')
    time.sleep(0.5)
    wildwood_badge = page.locator('#activeJobsCountBadge').inner_text()
    print(f"2. Search 'Wildwood' Active Jobs Badge: {wildwood_badge}")
    assert wildwood_badge == "22", f"Expected 22, got {wildwood_badge}"
    
    # 3. Clear search
    page.click('#clearSearchBtn')
    time.sleep(0.5)
    cleared_badge = page.locator('#activeJobsCountBadge').inner_text()
    print(f"3. Cleared Search Active Jobs Badge: {cleared_badge}")
    assert cleared_badge == "413", f"Expected 413, got {cleared_badge}"
    
    # 4. Filter Category I
    page.select_option('#categoryFilter', 'CATEGORY I')
    time.sleep(0.5)
    cat1_badge = page.locator('#activeJobsCountBadge').inner_text()
    print(f"4. Category I Active Jobs Badge: {cat1_badge}")
    assert cat1_badge == "26", f"Expected 26, got {cat1_badge}"
    
    # 5. Filter Category II
    page.select_option('#categoryFilter', 'CATEGORY II')
    time.sleep(0.5)
    cat2_badge = page.locator('#activeJobsCountBadge').inner_text()
    print(f"5. Category II Active Jobs Badge: {cat2_badge}")
    assert cat2_badge == "35", f"Expected 35, got {cat2_badge}"
    
    # 6. Filter Category III
    page.select_option('#categoryFilter', 'CATEGORY III')
    time.sleep(0.5)
    cat3_badge = page.locator('#activeJobsCountBadge').inner_text()
    print(f"6. Category III Active Jobs Badge: {cat3_badge}")
    assert cat3_badge == "352", f"Expected 352, got {cat3_badge}"
    
    # 7. Reset Category to ALL and toggle Full-Time Only
    page.select_option('#categoryFilter', 'ALL')
    time.sleep(0.5)
    page.click('#qualifyingOnlyCheck')
    time.sleep(0.5)
    ft_badge = page.locator('#activeJobsCountBadge').inner_text()
    print(f"7. Full-Time Only Active Jobs Badge: {ft_badge}")
    assert ft_badge == "297", f"Expected 297, got {ft_badge}"
    
    # 8. Type "Nurse" while Full-Time Only is checked
    page.fill('#searchInput', 'Nurse')
    time.sleep(0.5)
    nurse_badge = page.locator('#activeJobsCountBadge').inner_text()
    print(f"8. Full-Time 'Nurse' Active Jobs Badge: {nurse_badge}")
    assert int(nurse_badge) > 0 and int(nurse_badge) < 297, f"Expected nurse count between 0 and 297, got {nurse_badge}"
    
    # Take screenshot of filtered state
    page.screenshot(path='C:/Users/panda/.gemini/antigravity/brain/3c5b616f-75fb-4f0b-8bd7-178b6fbe7e52/dynamic_badge_test_preview.png', full_page=False)
    print("Screenshot saved to dynamic_badge_test_preview.png")
    
    browser.close()
    print("\nALL DYNAMIC BADGE & SEARCH TESTS PASSED!")
