# TVCS Qualifying Careers & Employer Search Engine

An automated job aggregator and HiringCafe-style searchable dashboard designed specifically to help parents and job seekers find and apply to positions that qualify dependents for enrollment in **The Villages Charter School (TVCS)** under Florida statutory employment criteria (§ 1002.33, Categories I–IV).

---

## What Sets This Engine Apart

1. **100% Verified, Real Postings (No Spam, No Fake Search Links)**:
   - Previous versions generated placeholder cards linking to general Google Search queries. 
   - Every single listing in this engine is an active, verified requisition sourced directly from official employer ATS portals (ADP Workforce Now, NEOGOV GovernmentJobs, Jacobs ATS).
2. **HiringCafe-Inspired Search Experience**:
   - Zero-latency, live client-side fuzzy search across job titles, schools, skills, departments, and commercial plazas.
   - One-click direct application links that take candidates straight to the employer's official application form.
   - Bookmarking & saved jobs system (stored in `localStorage`).
   - One-click CSV export of filtered positions and approved businesses.
3. **Dedicated TVCS Admission Qualification Filtering**:
   - **Full-Time Only Switch**: Florida law and TVCS policy strictly require continuous full-time employment (30+ hours/week) for school admission eligibility. The engine flags qualifying full-time roles vs. non-qualifying part-time roles.
   - **Priority Tier Tagging**: Visual badges highlighting Category I (1st lottery priority), Category II (Subcontractors - 2nd priority), Category III (Commercial plaza tenants), and Category IV (Approved vendors).
4. **Complete 432 Qualifying Employers Directory**:
   - Searchable directory of all 432 certified businesses across Lake Sumter Landing, Brownwood Paddock Square, Spanish Springs, Middleton Downtown, Magnolia Plaza, Sawgrass Grove, and Pinellas Plaza.
   - Shows active opening counts per company and provides direct links to each business's official career portal or contact page.

---

## TVCS Enrollment Categories Covered

| Category | Description | Admission Priority |
| :--- | :--- | :--- |
| **Category I** | Direct employees of The Villages of Lake-Sumter, Inc., Holding Company, TVCS instructional & operational staff, Properties of The Villages, and Recreation. | **Highest (1st Priority Lottery)** |
| **Category II** | Direct subcontractors performing continuous, full-time operational services (e.g. Jacobs Engineering / utilities, Sumter County BOCC). | **Priority (2nd Priority Lottery)** |
| **Category III** | Commercial tenants leasing physical commercial real estate in The Villages town squares and plazas. | **Priority (3rd Priority Lottery)** |
| **Category IV** | Approved vendors and regional business partners under continuous contract. | **Qualifying 4th Tier** |

> **Statutory Note**: Under Florida Statute § 1002.33, parents/guardians must maintain continuous full-time employment throughout their child's enrollment.

---

## Architecture & Data Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                   TVCS HARVEST PIPELINE (scraper.py)                   │
└────────────────────────────────────────────────────────────────────────┘
       │                                                   │
       ▼                                                   ▼
[Official ATS API Harvesters]             [Approved Employers Catalog]
- TVCS ADP API (cid: 9d9691d5...)         - 432 Certified TVCS Businesses
- The Villages ADP API (cid: ea774d...)   - Category Tier & Plaza Mapping
- Sumter County BOCC NEOGOV API           - Direct Corporate Web Links
- Jacobs Engineering ATS Harvester
       │                                                   │
       ▼                                                   ▼
 ┌───────────────┐                                   ┌────────────────┐
 │jobs_data.json │                                   │employers_data.json
 └───────────────┘                                   └────────────────┘
       │                                                   │
       └─────────────────────────┬─────────────────────────┘
                                 ▼
              ┌─────────────────────────────────────┐
              │ SQLite Database Sync (tvcs_jobs.db) │
              └─────────────────────────────────────┘
                                 │
                                 ▼
 ┌───────────────────────────────────────────────────────────────────────┐
 │                  FRONTEND INTERFACE (index.html)                      │
 │ - Live Fuzzy Search Bar (Title, Company, Plaza, Keyword)              │
 │ - Full-Time Qualifying Filter Switch (30+ hrs/wk statutory check)     │
 │ - Dual Tab Views: Active Verified Jobs vs. 432 Employers Directory    │
 │ - Bookmark & Application Status Tracking (localStorage)               │
 │ - Built-In TVCS Statutory Admission Rules Modal                       │
 └───────────────────────────────────────────────────────────────────────┘
```

---

## Local Setup & Quick Start

### 1. Prerequisites
- Python 3.11 or higher
- Git

### 2. Setup Virtual Environment & Install Dependencies
```bash
# Clone repository
git clone https://github.com/<your-username>/tvcs-qualifying-jobs.git
cd tvcs-qualifying-jobs

# Create virtual environment
python -m venv .venv

# Activate environment:
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

# Install requirements & Playwright browsers
pip install -r requirements.txt
playwright install chromium
```

### 3. Run the Scraper Pipeline
```bash
python scraper.py
```
This updates:
- `jobs_data.json` (Active verified requisitions)
- `employers_data.json` (Catalog of 432 certified businesses)
- `tvcs_jobs.db` (Synchronized SQLite database)

### 4. Open Dashboard
Open `index.html` in any modern web browser or serve locally via:
```bash
python -m http.server 8000
```
Then navigate to `http://localhost:8000`.

---

## Automated Daily Ingestion
The repository includes a GitHub Actions workflow (`.github/workflows/daily_scrape.yml`) that automatically runs `scraper.py` daily at 6:00 AM EST (10:00 UTC) and commits updated feeds directly to the repository.
