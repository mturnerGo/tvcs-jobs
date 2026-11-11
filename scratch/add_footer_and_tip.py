with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add CSS for btn-header-tip and site-footer
css_target = """        .btn-header-match:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(79, 70, 229, 0.35);
        }"""

css_replacement = """        .btn-header-match:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(79, 70, 229, 0.35);
        }

        .btn-header-tip {
            background: #fffbeb !important;
            color: #b45309 !important;
            border: 1px solid #fde68a !important;
            font-weight: 700 !important;
            transition: all 0.15s ease;
        }
        .btn-header-tip:hover {
            background: #fef3c7 !important;
            color: #92400e !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 10px rgba(245, 158, 11, 0.2);
        }

        /* --- Open Source Footer Styles --- */
        .site-footer {
            background: #ffffff;
            border-top: 1px solid var(--border-subtle);
            margin-top: 3.5rem;
            padding: 3rem 1.25rem 2rem 1.25rem;
            color: var(--text-body);
        }
        .footer-inner {
            max-width: 1400px;
            margin: 0 auto;
        }
        .footer-top-row {
            display: grid;
            grid-template-columns: 2fr 1.2fr 1.2fr;
            gap: 2.5rem;
            padding-bottom: 2rem;
            border-bottom: 1px solid var(--border-subtle);
        }
        .footer-links-title {
            font-size: 0.85rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: var(--text-heading);
            margin-bottom: 0.85rem;
        }
        .footer-links-list {
            list-style: none;
            padding: 0;
            margin: 0;
            display: flex;
            flex-direction: column;
            gap: 0.6rem;
        }
        .footer-links-list a {
            color: var(--text-muted);
            text-decoration: none;
            font-size: 0.85rem;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            transition: color 0.15s ease;
        }
        .footer-links-list a:hover {
            color: var(--primary);
        }
        .footer-tip-btn {
            background: #fef3c7;
            color: #b45309;
            border: 1px solid #fde68a;
            font-weight: 700;
            font-size: 0.82rem;
            padding: 0.35rem 0.75rem;
            border-radius: 6px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            transition: all 0.15s ease;
        }
        .footer-tip-btn:hover {
            background: #fde68a;
            color: #92400e;
        }
        .footer-bottom-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1.5rem;
            padding-top: 1.5rem;
            font-size: 0.8rem;
            color: #94a3b8;
            flex-wrap: wrap;
        }
        @media (max-width: 768px) {
            .footer-top-row { grid-template-columns: 1fr; gap: 1.5rem; }
            .footer-bottom-row { flex-direction: column; text-align: center; }
        }"""

assert css_target in html, "css_target not found"
html = html.replace(css_target, css_replacement, 1)

# 2. Add Official TVCS Portal link and Tip Jar button to header-actions
header_target = """            <div class="header-actions">
                <button class="btn-header btn-header-match" onclick="openModal('resumeModal')" title="Upload your resume to match with open positions">
                    <i class="fa-solid fa-wand-magic-sparkles"></i> Match My Resume
                </button>
                <button class="btn-header" onclick="openModal('rulesModal')">
                    <i class="fa-solid fa-scale-balanced"></i> Enrollment Rules
                </button>
                <button class="btn-header" onclick="switchTab('saved')">
                    <i class="fa-solid fa-bookmark"></i> Saved (<span id="savedCountHeader">0</span>)
                </button>
                <button class="btn-header btn-header-primary" onclick="exportFilteredData()">
                    <i class="fa-solid fa-download"></i> Export CSV
                </button>
            </div>"""

header_replacement = """            <div class="header-actions">
                <a href="https://www.tvcs.org/qualifying-businesses/" target="_blank" rel="noopener noreferrer" class="btn-header" style="text-decoration: none;" title="Official TVCS Qualifying Businesses Directory">
                    <i class="fa-solid fa-graduation-cap" style="color: #4f46e5;"></i> Official TVCS Portal <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 0.7rem; opacity: 0.7;"></i>
                </a>
                <button class="btn-header btn-header-match" onclick="openModal('resumeModal')" title="Upload your resume to match with open positions">
                    <i class="fa-solid fa-wand-magic-sparkles"></i> Match My Resume
                </button>
                <button class="btn-header" onclick="openModal('rulesModal')">
                    <i class="fa-solid fa-scale-balanced"></i> Enrollment Rules
                </button>
                <button class="btn-header" onclick="switchTab('saved')">
                    <i class="fa-solid fa-bookmark"></i> Saved (<span id="savedCountHeader">0</span>)
                </button>
                <button class="btn-header btn-header-primary" onclick="exportFilteredData()">
                    <i class="fa-solid fa-download"></i> Export CSV
                </button>
                <button class="btn-header btn-header-tip" onclick="openModal('tipModal')" title="Support this free open-source project">
                    <i class="fa-solid fa-mug-hot"></i> Tip Jar
                </button>
            </div>"""

assert header_target in html, "header_target not found"
html = html.replace(header_target, header_replacement, 1)

# 3. Add Official TVCS Directory pill into tvcs-banner
banner_target = """            <div style="display: flex; gap: 0.6rem; align-items: center; flex-wrap: wrap;">
                <div class="banner-pill">
                    785 Verified Employers
                </div>
                <button class="banner-pill" onclick="openModal('resumeModal')" style="cursor: pointer; background: rgba(255, 255, 255, 0.25); border: 1px solid rgba(255, 255, 255, 0.4); color: white; display: inline-flex; align-items: center; gap: 0.45rem;">
                    <i class="fa-solid fa-wand-magic-sparkles"></i> Resume Match
                </button>
            </div>"""

banner_replacement = """            <div style="display: flex; gap: 0.6rem; align-items: center; flex-wrap: wrap;">
                <div class="banner-pill">
                    785 Verified Employers
                </div>
                <a href="https://www.tvcs.org/qualifying-businesses/" target="_blank" rel="noopener noreferrer" class="banner-pill" style="cursor: pointer; background: rgba(255, 255, 255, 0.25); border: 1px solid rgba(255, 255, 255, 0.4); color: white; display: inline-flex; align-items: center; gap: 0.45rem; text-decoration: none;" title="Go to official TVCS Qualifying Businesses Directory">
                    <i class="fa-solid fa-arrow-up-right-from-square"></i> Official TVCS Directory
                </a>
                <button class="banner-pill" onclick="openModal('resumeModal')" style="cursor: pointer; background: rgba(255, 255, 255, 0.25); border: 1px solid rgba(255, 255, 255, 0.4); color: white; display: inline-flex; align-items: center; gap: 0.45rem;">
                    <i class="fa-solid fa-wand-magic-sparkles"></i> Resume Match
                </button>
            </div>"""

assert banner_target in html, "banner_target not found"
html = html.replace(banner_target, banner_replacement, 1)

# 4. Add open source footer right after .main-container
main_target = """        <!-- Pagination Controls Area -->
        <div id="paginationArea" class="pagination-bar" style="display: none;">
            <!-- Rendered via JS -->
        </div>

    </div>"""

main_replacement = """        <!-- Pagination Controls Area -->
        <div id="paginationArea" class="pagination-bar" style="display: none;">
            <!-- Rendered via JS -->
        </div>

    </div>

    <!-- Open Source & Community Footer -->
    <footer class="site-footer">
        <div class="footer-inner">
            <div class="footer-top-row">
                <div class="footer-brand">
                    <div style="display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.5rem;">
                        <span style="background: #4f46e5; color: white; width: 30px; height: 30px; border-radius: 8px; display: inline-flex; align-items: center; justify-content: center; font-size: 0.95rem;">
                            <i class="fa-solid fa-graduation-cap"></i>
                        </span>
                        <strong style="font-size: 1.1rem; color: var(--text-heading);">TVCS Qualifying Careers Discovery Engine</strong>
                    </div>
                    <p style="font-size: 0.85rem; color: var(--text-muted); line-height: 1.55; max-width: 520px; margin: 0 0 0.85rem 0;">
                        An independent, open-source community platform indexing real-time, direct-from-employer career openings across The Villages, Middleton, and Sumter County that qualify families for charter school enrollment under Florida Statute § 1002.33.
                    </p>
                    <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                        <a href="https://github.com/mturnerGo/vil-scraper" target="_blank" rel="noopener noreferrer" class="footer-tip-btn" style="background: #f1f5f9; color: var(--text-heading); border-color: var(--border-subtle); text-decoration: none;">
                            <i class="fa-brands fa-github"></i> Open Source Repository
                        </a>
                        <button type="button" onclick="openModal('tipModal')" class="footer-tip-btn">
                            <i class="fa-solid fa-mug-hot"></i> Support with a Coffee ($5)
                        </button>
                    </div>
                </div>

                <div class="footer-links-col">
                    <div class="footer-links-title">Official Portals &amp; Rules</div>
                    <ul class="footer-links-list">
                        <li>
                            <a href="https://www.tvcs.org/qualifying-businesses/" target="_blank" rel="noopener noreferrer">
                                <i class="fa-solid fa-graduation-cap"></i> Official TVCS Qualifying Partners Directory
                            </a>
                        </li>
                        <li>
                            <a href="https://www.tvcs.org/admission/" target="_blank" rel="noopener noreferrer">
                                <i class="fa-solid fa-file-circle-check"></i> Official TVCS Admissions Guidelines
                            </a>
                        </li>
                        <li>
                            <a href="https://www.thevillages.com/careers/" target="_blank" rel="noopener noreferrer">
                                <i class="fa-solid fa-building"></i> The Villages Corporate Careers
                            </a>
                        </li>
                    </ul>
                </div>

                <div class="footer-links-col">
                    <div class="footer-links-title">Community &amp; Code</div>
                    <ul class="footer-links-list">
                        <li>
                            <a href="https://github.com/mturnerGo/vil-scraper" target="_blank" rel="noopener noreferrer">
                                <i class="fa-brands fa-github"></i> Star &amp; Fork on GitHub (MIT License)
                            </a>
                        </li>
                        <li>
                            <a href="https://github.com/mturnerGo/vil-scraper/issues" target="_blank" rel="noopener noreferrer">
                                <i class="fa-solid fa-bug"></i> Suggest an Employer / File Issue
                            </a>
                        </li>
                        <li>
                            <button type="button" onclick="openModal('resumeModal')" style="background: none; border: none; padding: 0; color: var(--primary); font-size: 0.85rem; cursor: pointer; display: inline-flex; align-items: center; gap: 0.45rem; font-weight: 600;">
                                <i class="fa-solid fa-wand-magic-sparkles"></i> Match Jobs to Your Resume
                            </button>
                        </li>
                    </ul>
                </div>
            </div>

            <div class="footer-bottom-row">
                <div class="footer-opensource-blurb">
                    <span><i class="fa-brands fa-creative-commons"></i> <strong>Open Source Community Tool:</strong> Built independently to empower parents and families. Not officially affiliated with or endorsed by The Villages Charter School, Inc. or The Villages of Lake-Sumter, Inc.</span>
                </div>
                <div class="footer-copy">
                    <span>© 2026 TVCS Careers Engine · Free &amp; Open Source</span>
                </div>
            </div>
        </div>
    </footer>"""

assert main_target in html, "main_target not found"
html = html.replace(main_target, main_replacement, 1)

# 5. Add official links to rulesModal
rules_target = """            <div style="background: #fef3c7; border: 1px solid #fde68a; border-radius: 8px; padding: 1rem; margin-top: 1rem; font-size: 0.85rem; color: #92400e;">
                <strong><i class="fa-solid fa-triangle-exclamation"></i> Mandatory Full-Time Requirement:</strong>
                Florida statutory guidelines require continuous <strong>full-time</strong> employment (typically 30–40 hours/week) during the student's enrollment. Part-time positions do not meet school eligibility requirements.
            </div>
        </div>
    </div>"""

rules_replacement = """            <div style="background: #fef3c7; border: 1px solid #fde68a; border-radius: 8px; padding: 1rem; margin-top: 1rem; font-size: 0.85rem; color: #92400e;">
                <strong><i class="fa-solid fa-triangle-exclamation"></i> Mandatory Full-Time Requirement:</strong>
                Florida statutory guidelines require continuous <strong>full-time</strong> employment (typically 30–40 hours/week) during the student's enrollment. Part-time positions do not meet school eligibility requirements.
            </div>

            <div style="display: flex; gap: 0.75rem; margin-top: 1.25rem; flex-wrap: wrap;">
                <a href="https://www.tvcs.org/qualifying-businesses/" target="_blank" rel="noopener noreferrer" class="btn-employer-site" style="background: var(--primary); color: white; border: none; text-decoration: none; padding: 0.65rem 1rem; font-weight: 700; font-size: 0.85rem; display: inline-flex; align-items: center; gap: 0.45rem;">
                    <i class="fa-solid fa-graduation-cap"></i> View Official TVCS Qualifying Partners Directory <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 0.7rem;"></i>
                </a>
                <a href="https://www.tvcs.org/admission/" target="_blank" rel="noopener noreferrer" class="btn-employer-site" style="background: #f1f5f9; color: var(--text-heading); border: 1px solid var(--border-subtle); text-decoration: none; padding: 0.65rem 1rem; font-weight: 600; font-size: 0.85rem; display: inline-flex; align-items: center; gap: 0.45rem;">
                    Official TVCS Admissions Guidelines <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 0.7rem;"></i>
                </a>
            </div>
        </div>
    </div>"""

assert rules_target in html, "rules_target not found"
html = html.replace(rules_target, rules_replacement, 1)

# 6. Add tipModal right after resumeModal and before #toast
toast_target = """    <!-- Toast Notification -->
    <div id="toast" class="toast">"""

toast_replacement = """    <!-- Modal: Tip Jar & Creator Support -->
    <div id="tipModal" class="modal-backdrop" onclick="closeModalOnBackdrop(event, 'tipModal')">
        <div class="modal-box" style="max-width: 520px; text-align: center;">
            <button class="modal-close-btn" onclick="closeModal('tipModal')"><i class="fa-solid fa-xmark"></i></button>
            <div style="width: 58px; height: 58px; background: #fef3c7; color: #d97706; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 1.6rem; margin-bottom: 0.85rem;">
                <i class="fa-solid fa-mug-hot"></i>
            </div>
            <h3 style="margin: 0 0 0.5rem 0; font-size: 1.35rem; justify-content: center; color: var(--text-heading);">Support This Community Tool</h3>
            <p style="font-size: 0.88rem; color: var(--text-body); line-height: 1.55; margin-bottom: 1.5rem; text-align: left;">
                This project was created independently as an open-source tool to help local parents easily discover real, verified full-time jobs that qualify their children for <strong>The Villages Charter School (TVCS)</strong> admission under Florida Statute § 1002.33.
                <br><br>
                If this tool saved you hours of searching or helped you land a job, buying a coffee helps support ongoing data indexing, automated scrapers, and new features!
            </p>

            <div style="display: flex; flex-direction: column; gap: 0.75rem;">
                <!-- Buy Me a Coffee Option -->
                <a id="bmcLink" href="https://buymeacoffee.com/marcusturner" target="_blank" rel="noopener noreferrer" class="btn-employer-site" style="background: #FFDD00; color: #000000; justify-content: center; padding: 0.85rem; font-weight: 800; border: none; font-size: 0.95rem; text-decoration: none; box-shadow: 0 3px 10px rgba(255, 221, 0, 0.35);">
                    <i class="fa-solid fa-coffee"></i> Buy Me a Coffee ($5)
                </a>

                <!-- Ko-fi Option -->
                <a id="kofiLink" href="https://ko-fi.com/marcusturner" target="_blank" rel="noopener noreferrer" class="btn-employer-site" style="background: #13C3FF; color: #ffffff; justify-content: center; padding: 0.85rem; font-weight: 700; border: none; font-size: 0.95rem; text-decoration: none; box-shadow: 0 3px 10px rgba(19, 195, 255, 0.25);">
                    <i class="fa-solid fa-heart"></i> Support via Ko-fi
                </a>
            </div>

            <div style="margin-top: 1.25rem; font-size: 0.78rem; color: var(--text-muted);">
                <i class="fa-brands fa-github"></i> 100% Free &amp; Open Source · Contributions and issue reports welcome on GitHub.
            </div>
        </div>
    </div>

    <!-- Toast Notification -->
    <div id="toast" class="toast">"""

assert toast_target in html, "toast_target not found"
html = html.replace(toast_target, toast_replacement, 1)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Applied footer, tipModal, and official TVCS links successfully!")
