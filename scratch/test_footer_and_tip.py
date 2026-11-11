from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1400, 'height': 1100})
    
    print("Navigating to http://localhost:8000...")
    page.goto('http://localhost:8000', timeout=15000)
    page.wait_for_selector('.job-card', timeout=10000)
    time.sleep(1)
    
    # 1. Verify Official TVCS links in Header and Banner
    header_tvcs = page.locator('header a[href*="tvcs.org/qualifying-businesses"]')
    assert header_tvcs.count() > 0, "Official TVCS portal link missing in header!"
    print("✓ Header Official TVCS Link Verified:", header_tvcs.first.get_attribute('href'))
    
    banner_tvcs = page.locator('.tvcs-banner a[href*="tvcs.org/qualifying-businesses"]')
    assert banner_tvcs.count() > 0, "Official TVCS directory link missing in banner!"
    print("✓ Banner Official TVCS Link Verified:", banner_tvcs.first.get_attribute('href'))
    
    # 2. Test Tip Jar Modal
    print("Opening Tip Jar Modal...")
    page.click('.btn-header-tip')
    time.sleep(0.5)
    assert page.is_visible('#tipModal.open'), "Tip jar modal did not open!"
    
    bmc_link = page.locator('#bmcLink').get_attribute('href')
    kofi_link = page.locator('#kofiLink').get_attribute('href')
    print(f"✓ Tip Modal Links: BMC='{bmc_link}', Ko-fi='{kofi_link}'")
    assert "buymeacoffee.com" in bmc_link, "Buy Me a Coffee link missing!"
    assert "ko-fi.com" in kofi_link, "Ko-fi link missing!"
    
    # Screenshot of Tip Modal
    page.screenshot(path='C:/Users/panda/.gemini/antigravity/brain/3c5b616f-75fb-4f0b-8bd7-178b6fbe7e52/tip_jar_modal_preview.png', full_page=False)
    print("✓ Saved tip jar modal screenshot to tip_jar_modal_preview.png")
    
    # Close modal
    page.click('#tipModal .modal-close-btn')
    time.sleep(0.4)
    
    # 3. Verify Open Source Footer
    footer = page.locator('.site-footer')
    assert footer.count() > 0, "Site footer is missing!"
    
    github_link = page.locator('.site-footer a[href*="github.com/mturnerGo/vil-scraper"]')
    assert github_link.count() > 0, "GitHub repository link missing in footer!"
    print("✓ GitHub Open Source Link Verified:", github_link.first.get_attribute('href'))
    
    footer_tvcs = page.locator('.site-footer a[href*="tvcs.org/qualifying-businesses"]')
    assert footer_tvcs.count() > 0, "Official TVCS link missing in footer!"
    print("✓ Footer Official TVCS Directory Verified:", footer_tvcs.first.get_attribute('href'))
    
    # Scroll to footer and take screenshot
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(0.5)
    page.screenshot(path='C:/Users/panda/.gemini/antigravity/brain/3c5b616f-75fb-4f0b-8bd7-178b6fbe7e52/open_source_footer_preview.png', full_page=False)
    print("✓ Saved open source footer screenshot to open_source_footer_preview.png")
    
    browser.close()
    print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")
