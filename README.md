# TVCS Qualifying Careers & Employer Search Engine

An automated job aggregator and searchable dashboard designed specifically to help parents and job seekers find and apply to positions that qualify dependents for enrollment in **The Villages Charter School (TVCS)** under Florida statutory employment criteria (§ 1002.33, Categories I–IV).

Live Deployment: [https://mturnergo.github.io/tvcs-jobs/](https://mturnergo.github.io/tvcs-jobs/)

---

## What Sets This Engine Apart

1. **570+ Verified, Real Active Postings (No Spam, No Fake Search Links)**:
   - Sourced directly from official enterprise ATS endpoints:
     - **iCIMS REST API** (UF Health The Villages Hospital — 316+ openings)
     - **UKG Pro / UltiPro** (Seacoast National Bank — 69+ openings)
     - **Workday CXS API** (The Villages Health / CenterWell, Florida Cancer Specialists, Target Rolling Acres Plaza, Massey Services)
     - **TalentBrew / Radancy Driver** (AT&T Lake Sumter Landing & Brownwood)
     - **ADP Workforce Now API** (The Villages Charter School, The Villages Operating Entities, VCCDD, Concierge Homecare)
     - **NEOGOV API** (City of Wildwood, Lake-Sumter State College, Sumter County BOCC)
     - **ClearCompany API** (FMK Restaurant Group: Bonifay, Chop House, Evans Prairie, Bluefin Grill)
     - **Greenhouse Board API** (Toojay's Gourmet Deli — Lake Sumter Landing & Brownwood)
     - **Paylocity State Parser** (Oak & Stone Eastport)
     - **Dayforce HCM Headless Driver** (Down To Earth Landscaping & Golf Operations)
2. **Universal Autonomous Harvester (HiringCafe-Style Ingestion)**:
   - Evaluates any company website automatically: detects underlying ATS engines, extracts Schema.org `JobPosting` JSON-LD structured data, applies geographic boundary filters for The Villages and surrounding municipalities, and categorizes jobs without custom code.
3. **Dedicated TVCS Admission Qualification Filtering**:
   - **Priority Tier Badges**: Visual indicators highlighting Category I (1st lottery priority), Category II (Subcontractors - 2nd priority), Category III (Commercial plaza tenants), and Category IV (Approved vendors).
4. **Complete 785 Qualifying Employers Directory**:
   - Searchable directory of all 785 certified businesses across Lake Sumter Landing, Brownwood Paddock Square, Spanish Springs, Middleton Downtown, Magnolia Plaza, Sawgrass Grove, and Pinellas Plaza.
   - Shows active opening counts per company and provides direct links to each business's official career portal or contact page.

---

## TVCS Enrollment Categories Covered

| Category | Official Definition | Admission Priority |
| :--- | :--- | :--- |
| **Category I** | A Villages’ Company or Salesperson under contract with Properties of The Villages. | **Highest Priority** |
| **Category II** | **Business Partner Sub-Contractors**: Business Partners under direct contract, other than a lease, with a Villages’ Company providing independent contractor, construction, maintenance, consulting, or other similar services in support of Villages’ Projects. (Services must be regular, ongoing, and paid directly by a Villages’ Company, or meet the Minimum Threshold Percentage). | **2nd Priority** |
| **Category III** | Business Partners who lease directly from one of the commercial real estate entities in a Villages’ company. | **3rd Priority** |
| **Category IV** | Business Partners that own or lease a permanent business site from a non-Villages’ entity, from which they operate their business within The Villages (reviewed and confirmed by the TVCS Enrollment Committee). | **4th Priority** |

> **Official Criteria Note**: Admission qualification is governed by direct employer categorization with a Villages' Company and official TVCS Enrollment Committee review.

---

## Architecture & Data Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│               TVCS MASTER PIPELINE (engine/pipeline.py)                │
└────────────────────────────────────────────────────────────────────────┘
       │                                                   │
       ▼                                                   ▼
[Enterprise ATS Protocol Drivers]             [Autonomous Harvester Engine]
- iCIMS Jibe (UF Health)                      - engine/universal_harvester.py
- Workday CXS (CenterWell, FCS, Massey)       - Schema.org JobPosting JSON-LD
- ADP WFN (TVCS, VCCDD, Operating, Concierge) - Greenhouse API (Toojays)
- ClearCompany API (FMK Hospitality)          - Paylocity Parser (Oak & Stone)
- UltiPro UKG (Seacoast Bank)                 - Dayforce Playwright (DTE)
- NEOGOV API (Wildwood, Sumter, LSSC)
       │                                                   │
       └─────────────────────────┬─────────────────────────┘
                                 ▼
                     [Whitelist Matcher Engine]
                     - 785 Certified TVCS Employers
                     - Statutory Category & Tier Assignment
                                 ▼
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼
   jobs_data.json                                  employers_data.json
   (560+ Active Jobs)                              (785 Verified Employers)
         │                                               │
         └───────────────────────┬───────────────────────┘
                                 ▼
               ┌───────────────────────────────────┐
               │  SQLite Database (tvcs_jobs.db)   │
               └───────────────────────────────────┘
                                 │
                                 ▼
 ┌───────────────────────────────────────────────────────────────────────┐
 │                  FRONTEND INTERFACE (index.html)                      │
 │ - Live Fast Fuzzy Search (Title, Company, Plaza, Keyword)             │
 │ - Full-Time Schedule Filter Switch                                    │
 │ - Client-Side Private Resume Parser (.docx, .doc, .pdf, .txt)         │
 │ - Dual Tab Views: 560+ Active Jobs vs. 785 Employers Directory        │
 │ - In-App GitHub Issue & Support Modal Form                            │
 │ - Statutory Category Rules Information Modal                          │
 └───────────────────────────────────────────────────────────────────────┘
```

---

## Autonomous Harvester CLI Usage

To discover and ingest job postings for any company without modifying code:
```bash
# Ingest single company by URL
python -m engine.universal_harvester --company "New Company Name" --url "https://company.com/careers"

# Harvest all discovered ATS endpoints
python -m engine.universal_harvester --harvest-all
```

---

## Automated Daily Ingestion
The repository includes a GitHub Actions workflow (`.github/workflows/daily_scrape.yml`) that automatically runs `python engine/pipeline.py` daily at 6:00 AM EST (10:00 UTC) and commits updated feeds directly to the repository.
