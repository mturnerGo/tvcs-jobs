import re

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. State variables in script
old_vars = "let allJobs = [];\n        let allEmployers = [];\n        let savedJobIds = new Set();\n        let currentTab = 'jobs';"
new_vars = """let allJobs = [];
        let allEmployers = [];
        let savedJobIds = new Set();
        let currentTab = 'jobs';
        let resumeMatchedJobs = null;
        let selectedResumeFile = null;

        // Resume Matcher View Switching
        function switchResumeTab(mode) {
            const fileSec = document.getElementById('resumeFileSection');
            const pasteSec = document.getElementById('resumePasteSection');
            const fileBtn = document.getElementById('resumeTabFileBtn');
            const pasteBtn = document.getElementById('resumeTabPasteBtn');

            if (mode === 'file') {
                fileSec.style.display = 'block';
                pasteSec.style.display = 'none';
                fileBtn.classList.add('active');
                pasteBtn.classList.remove('active');
            } else {
                fileSec.style.display = 'none';
                pasteSec.style.display = 'block';
                fileBtn.classList.remove('active');
                pasteBtn.classList.add('active');
            }
        }

        function handleResumeFileSelect(e) {
            const file = e.target.files[0];
            if (!file) return;
            setResumeFile(file);
        }

        function setResumeFile(file) {
            selectedResumeFile = file;
            document.getElementById('selectedFileName').innerText = file.name;
            document.getElementById('selectedFileSize').innerText = `(${(file.size / 1024).toFixed(1)} KB)`;
            document.getElementById('selectedFileInfo').style.display = 'flex';
            document.getElementById('resumeDropzone').style.borderColor = '#10b981';
        }

        function clearSelectedFile() {
            selectedResumeFile = null;
            document.getElementById('resumeFileInput').value = '';
            document.getElementById('selectedFileInfo').style.display = 'none';
            document.getElementById('resumeDropzone').style.borderColor = '#cbd5e1';
        }

        async function extractResumeText() {
            const isPasteActive = document.getElementById('resumePasteSection').style.display === 'block';
            if (isPasteActive) {
                const text = document.getElementById('resumePasteText').value.trim();
                if (!text) {
                    showToast("Please paste your resume text to match.");
                    return null;
                }
                return text;
            }

            if (!selectedResumeFile) {
                const pasteVal = document.getElementById('resumePasteText').value.trim();
                if (pasteVal) return pasteVal;
                showToast("Please choose a resume file (.pdf, .txt) or paste your resume text.");
                return null;
            }

            const file = selectedResumeFile;
            const fileName = file.name.toLowerCase();

            // Text or Markdown
            if (fileName.endsWith('.txt') || fileName.endsWith('.md') || file.type.includes('text')) {
                return await file.text();
            }

            // PDF extraction
            if (fileName.endsWith('.pdf') || file.type.includes('pdf')) {
                if (typeof pdfjsLib === 'undefined') {
                    showToast("PDF parser loading... Please paste your text if this takes longer than 2 seconds.");
                    return null;
                }
                try {
                    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
                    const arrayBuffer = await file.arrayBuffer();
                    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
                    let text = '';
                    for (let i = 1; i <= pdf.numPages; i++) {
                        const page = await pdf.getPage(i);
                        const content = await page.getTextContent();
                        text += content.items.map(it => it.str).join(' ') + '\\n';
                    }
                    return text;
                } catch (err) {
                    console.error("PDF parsing error:", err);
                    showToast("Could not parse this PDF. Please copy-paste your resume into the Paste tab.");
                    return null;
                }
            }

            return await file.text();
        }

        function calculateResumeMatches(resumeText, fullTimeOnly = true, minScoreThreshold = 40) {
            const stopWords = new Set([
                'and','the','for','with','in','of','to','at','a','or','on','is','as','an','by','be','are','this','that','our','all','from',
                'with','your','has','have','will','was','were','their','them','about','been','able','must','should','would','they'
            ]);

            const cleanText = resumeText.toLowerCase().replace(/[^a-z0-9\\s]/g, ' ');
            const words = cleanText.split(/\\s+/).filter(w => w.length > 0);
            const resumeTokens = new Set(words.filter(w => w.length > 2 && !stopWords.has(w)));

            // 2-word and 3-word n-grams
            const ngrams = new Set();
            for (let i = 0; i < words.length - 1; i++) {
                const w1 = words[i], w2 = words[i+1];
                if (w1.length > 2 && w2.length > 2) {
                    ngrams.add(`${w1} ${w2}`);
                }
                if (i < words.length - 2) {
                    const w3 = words[i+2];
                    if (w1.length > 2 && w2.length > 2 && w3.length > 2) {
                        ngrams.add(`${w1} ${w2} ${w3}`);
                    }
                }
            }

            const scored = [];

            for (const job of allJobs) {
                if (fullTimeOnly && !job.TVCS_Qualifying) continue;

                const titleLower = job.Job_Title.toLowerCase();
                const descLower = (job.Description || '').toLowerCase();
                const compLower = job.Company.toLowerCase();
                const locLower = (job.Plaza_Location || '').toLowerCase();
                const fullJobText = `${titleLower} ${compLower} ${descLower} ${locLower}`;

                let score = 0;
                const matchedSkills = [];

                // N-gram multi-word match
                for (const ng of ngrams) {
                    if (titleLower.includes(ng)) {
                        score += 35;
                        if (!matchedSkills.includes(ng) && matchedSkills.length < 5) matchedSkills.push(ng);
                    } else if (descLower.includes(ng) || fullJobText.includes(ng)) {
                        score += 15;
                        if (!matchedSkills.includes(ng) && matchedSkills.length < 5) matchedSkills.push(ng);
                    }
                }

                // Single word match
                const jobTokens = new Set(fullJobText.replace(/[^a-z0-9\\s]/g, ' ').split(/\\s+/).filter(w => w.length > 2 && !stopWords.has(w)));
                for (const token of jobTokens) {
                    if (resumeTokens.has(token)) {
                        if (titleLower.includes(token)) {
                            score += 18;
                            if (!matchedSkills.includes(token) && matchedSkills.length < 5) matchedSkills.push(token);
                        } else if (compLower.includes(token)) {
                            score += 8;
                        } else {
                            score += 4;
                            if (!matchedSkills.includes(token) && matchedSkills.length < 5) matchedSkills.push(token);
                        }
                    }
                }

                // TVCS Category Priority Boost
                if (job.Category === 'CATEGORY I') score += 12;
                else if (job.Category === 'CATEGORY II') score += 8;
                else if (job.Category === 'CATEGORY III') score += 5;

                // Full-time compliance boost
                if (job.TVCS_Qualifying) score += 10;

                // Normalize percentage (20% - 98%)
                const percentage = Math.min(98, Math.max(15, Math.round((score / 125) * 100)));

                if (percentage >= minScoreThreshold) {
                    scored.push({
                        ...job,
                        matchScore: percentage,
                        matchedSkills: matchedSkills
                    });
                }
            }

            // Sort descending by matchScore, then by TVCS Priority Tier
            scored.sort((a, b) => {
                if (b.matchScore !== a.matchScore) return b.matchScore - a.matchScore;
                return a.Priority_Tier - b.Priority_Tier;
            });

            return scored;
        }

        async function processResumeMatch() {
            const btn = document.getElementById('btnRunResumeMatch');
            const originalHtml = btn.innerHTML;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing Resume...';
            btn.disabled = true;

            try {
                const resumeText = await extractResumeText();
                if (!resumeText || resumeText.length < 25) {
                    showToast("Please provide more resume text (at least 25 characters) to analyze.");
                    btn.innerHTML = originalHtml;
                    btn.disabled = false;
                    return;
                }

                const fullTimeOnly = document.getElementById('resumeFullTimeOnly').checked;
                const minThreshold = parseInt(document.getElementById('resumeMinMatch').value, 10) || 40;

                const matches = calculateResumeMatches(resumeText, fullTimeOnly, minThreshold);

                if (matches.length === 0) {
                    showToast("No positions met the minimum match threshold. Try selecting Broad relevance.");
                    btn.innerHTML = originalHtml;
                    btn.disabled = false;
                    return;
                }

                resumeMatchedJobs = matches;
                closeModal('resumeModal');
                switchTab('jobs');

                // Display active match banner
                const banner = document.getElementById('resumeMatchBanner');
                banner.style.display = 'flex';
                document.getElementById('resumeMatchCount').innerText = matches.length;

                showToast(`Found ${matches.length} matching jobs for your resume!`);
                applyFilters(true);
            } catch (e) {
                console.error("Error processing resume:", e);
                showToast("Failed to analyze resume. Please try pasting text.");
            } finally {
                btn.innerHTML = originalHtml;
                btn.disabled = false;
            }
        }

        function clearResumeMatch() {
            resumeMatchedJobs = null;
            document.getElementById('resumeMatchBanner').style.display = 'none';
            showToast("Cleared resume matching filter");
            applyFilters(true);
        }"""

assert old_vars in content, "old_vars not found!"
content = content.replace(old_vars, new_vars, 1)

# 2. Update updateTabCounters to respect resumeMatchedJobs
old_counters = """        function updateTabCounters(searchVal, qualifyingOnly, activelyHiringOnly, categoryVal, plazaVal, employerVal) {
            // Count matching active jobs
            const matchingJobsCount = allJobs.filter(job => {"""

new_counters = """        function updateTabCounters(searchVal, qualifyingOnly, activelyHiringOnly, categoryVal, plazaVal, employerVal) {
            const jobsPool = (!savedOnlyActive() && resumeMatchedJobs) ? resumeMatchedJobs : allJobs;
            // Count matching active jobs
            const matchingJobsCount = jobsPool.filter(job => {"""

def savedOnlyActive():
    pass

# Let's inspect updateTabCounters in content
old_tab_counters = """        function updateTabCounters(searchVal, qualifyingOnly, activelyHiringOnly, categoryVal, plazaVal, employerVal) {
            // Count matching active jobs
            const matchingJobsCount = allJobs.filter(job => {"""

new_tab_counters = """        function updateTabCounters(searchVal, qualifyingOnly, activelyHiringOnly, categoryVal, plazaVal, employerVal) {
            const jobsPool = (currentTab !== 'saved' && resumeMatchedJobs) ? resumeMatchedJobs : allJobs;
            // Count matching active jobs
            const matchingJobsCount = jobsPool.filter(job => {"""

assert old_tab_counters in content, "old_tab_counters not found!"
content = content.replace(old_tab_counters, new_tab_counters, 1)

# 3. Update renderJobs to use jobsPool and show matchScore / matchedSkills
old_render_jobs = """        function renderJobs(searchVal, qualifyingOnly, categoryVal, plazaVal, employerVal, savedOnly = false) {
            const container = savedOnly ? document.getElementById('savedView') : document.getElementById('jobsView');

            const filtered = allJobs.filter(job => {"""

new_render_jobs = """        function renderJobs(searchVal, qualifyingOnly, categoryVal, plazaVal, employerVal, savedOnly = false) {
            const container = savedOnly ? document.getElementById('savedView') : document.getElementById('jobsView');
            const jobsPool = (!savedOnly && resumeMatchedJobs) ? resumeMatchedJobs : allJobs;

            const filtered = jobsPool.filter(job => {"""

assert old_render_jobs in content, "old_render_jobs not found!"
content = content.replace(old_render_jobs, new_render_jobs, 1)

# 4. Update the card template inside renderJobs to display matchScore and matchedSkills
old_card_badges = """                            <div class="card-badges-row">
                                <span class="priority-badge ${catClass}">
                                    <i class="fa-solid fa-award"></i> ${job.Priority_Label || job.Category}
                                </span>"""

new_card_badges = """                            <div class="card-badges-row">
                                ${job.matchScore ? `
                                    <span class="match-score-badge" title="Compatibility with your uploaded resume">
                                        <i class="fa-solid fa-star"></i> ${job.matchScore}% Match
                                    </span>
                                ` : ''}
                                <span class="priority-badge ${catClass}">
                                    <i class="fa-solid fa-award"></i> ${job.Priority_Label || job.Category}
                                </span>"""

assert old_card_badges in content, "old_card_badges not found!"
content = content.replace(old_card_badges, new_card_badges, 1)

old_card_company = """                            <div class="company-name">
                                <i class="fa-regular fa-building"></i> ${escapeHtml(job.Company)}
                            </div>"""

new_card_company = """                            <div class="company-name">
                                <i class="fa-regular fa-building"></i> ${escapeHtml(job.Company)}
                            </div>

                            ${job.matchedSkills && job.matchedSkills.length > 0 ? `
                                <div class="matched-skills-box">
                                    <span class="matched-skills-label"><i class="fa-solid fa-check-double"></i> Matched Resume Skills:</span>
                                    <div class="matched-skills-list">
                                        ${job.matchedSkills.map(s => `<span class="skill-chip">${escapeHtml(s)}</span>`).join('')}
                                    </div>
                                </div>
                            ` : ''}"""

assert old_card_company in content, "old_card_company not found!"
content = content.replace(old_card_company, new_card_company, 1)

# 5. Add dropzone drag-and-drop listener to DOMContentLoaded
old_dom_init = "document.addEventListener('DOMContentLoaded', initData);"
new_dom_init = """document.addEventListener('DOMContentLoaded', () => {
            initData();

            // Resume Drag & Drop Setup
            const dropzone = document.getElementById('resumeDropzone');
            if (dropzone) {
                ['dragenter', 'dragover'].forEach(name => {
                    dropzone.addEventListener(name, (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        dropzone.classList.add('dragover');
                    });
                });
                ['dragleave', 'drop'].forEach(name => {
                    dropzone.addEventListener(name, (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        dropzone.classList.remove('dragover');
                    });
                });
                dropzone.addEventListener('drop', (e) => {
                    const dt = e.dataTransfer;
                    if (dt.files && dt.files.length > 0) {
                        setResumeFile(dt.files[0]);
                    }
                });
            }
        });"""

assert old_dom_init in content, "old_dom_init not found!"
content = content.replace(old_dom_init, new_dom_init, 1)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated index.html with Resume Matcher successfully!")
