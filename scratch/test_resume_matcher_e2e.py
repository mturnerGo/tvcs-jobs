from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1400, 'height': 1000})
    
    print("Navigating to http://localhost:8000...")
    page.goto('http://localhost:8000', timeout=15000)
    page.wait_for_selector('.job-card', timeout=10000)
    time.sleep(1)
    
    # 1. Click "Match My Resume"
    print("Opening Resume Matcher Modal...")
    page.click('.btn-header-match')
    time.sleep(0.5)
    assert page.is_visible('#resumeModal.open'), "Resume modal did not open!"
    
    # 2. Switch to Paste Tab
    page.click('#resumeTabPasteBtn')
    time.sleep(0.3)
    
    # 3. Paste Healthcare Resume
    nurse_resume = """
    Jane Doe, RN, BSN
    Registered Nurse with 7 years of intensive clinical hospital experience in Emergency Medicine and Critical Care.
    Certifications: BLS, ACLS, Florida Registered Nursing License.
    Skills: Emergency Triage, Patient Assessment, ICU Care, EMR Documentation, Acute Patient Management.
    Extensive background in hospital clinical care.
    """
    page.fill('#resumePasteText', nurse_resume)
    time.sleep(0.3)
    
    # 4. Click Find Best Job Matches
    print("Running Resume Matching for Healthcare/Nurse profile...")
    page.click('#btnRunResumeMatch')
    time.sleep(1)
    
    # 5. Verify Match Banner is visible
    assert page.is_visible('#resumeMatchBanner'), "Resume match banner is not visible!"
    match_count_text = page.locator('#resumeMatchCount').inner_text()
    print(f"Resume Matches Found: {match_count_text}")
    assert int(match_count_text) > 0, "No matches found for nurse resume!"
    
    # Check first job card
    first_card = page.locator('.job-card').first
    first_title = first_card.locator('.job-title').inner_text()
    first_score = first_card.locator('.match-score-badge').inner_text()
    first_skills = first_card.locator('.skill-chip').all_inner_texts()
    
    print(f"Top Matched Job: {first_title}")
    print(f"Match Score: {first_score}")
    print(f"Matched Skills: {first_skills}")
    
    assert "Nurse" in first_title or "RN" in first_title or "Emergency" in first_title or "Care" in first_title, f"Unexpected top job: {first_title}"
    assert "% Match" in first_score, f"Unexpected score: {first_score}"
    assert len(first_skills) > 0, "No skill chips rendered!"
    
    # Screenshot of Nurse Match View
    page.screenshot(path='C:/Users/panda/.gemini/antigravity/brain/3c5b616f-75fb-4f0b-8bd7-178b6fbe7e52/resume_match_nurse_preview.png', full_page=False)
    print("Saved screenshot to resume_match_nurse_preview.png")
    
    # 6. Test Clear Match Filter
    print("Clearing match filter...")
    page.click('.btn-clear-match')
    time.sleep(0.5)
    assert not page.is_visible('#resumeMatchBanner'), "Match banner still visible after clear!"
    restored_badge = page.locator('#activeJobsCountBadge').inner_text()
    print(f"Restored Active Jobs Badge: {restored_badge}")
    assert restored_badge == "413", f"Expected 413, got {restored_badge}"
    
    # 7. Test Banking Profile
    print("Testing Banking Profile Match...")
    page.click('.btn-header-match')
    time.sleep(0.3)
    page.click('#resumeTabPasteBtn')
    time.sleep(0.2)
    banking_resume = """
    John Smith - Commercial & Retail Banking Specialist
    5 years experience at Seacoast Bank as Branch Teller, Consumer Banker, and Loan Coordinator.
    Skills: Cash Handling, Account Management, Branch Operations, Customer Service, Deposit Processing, Banking Compliance.
    """
    page.fill('#resumePasteText', banking_resume)
    page.click('#btnRunResumeMatch')
    time.sleep(1)
    
    bank_match_count = page.locator('#resumeMatchCount').inner_text()
    print(f"Banking Matches Found: {bank_match_count}")
    top_bank_job = page.locator('.job-card').first
    top_bank_title = top_bank_job.locator('.job-title').inner_text()
    top_bank_score = top_bank_job.locator('.match-score-badge').inner_text()
    top_bank_skills = top_bank_job.locator('.skill-chip').all_inner_texts()
    
    print(f"Top Banking Job: {top_bank_title}")
    print(f"Banking Match Score: {top_bank_score}")
    print(f"Banking Matched Skills: {top_bank_skills}")
    
    assert "Bank" in top_bank_title or "Seacoast" in top_bank_title, f"Expected Banking job, got: {top_bank_title}"
    
    # Screenshot of Banking Match View
    page.screenshot(path='C:/Users/panda/.gemini/antigravity/brain/3c5b616f-75fb-4f0b-8bd7-178b6fbe7e52/resume_match_banking_preview.png', full_page=False)
    print("Saved screenshot to resume_match_banking_preview.png")
    
    browser.close()
    print("\nALL RESUME MATCHING END-TO-END TESTS PASSED SUCCESSFULLY!")
