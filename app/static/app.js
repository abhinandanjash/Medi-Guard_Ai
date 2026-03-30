/* ═══════════════════════════════════════════════════════════
   Medi-Guard AI — Premium Frontend Application v3.0
   Split Submit / Pre-Adjudication Workflow
   ═══════════════════════════════════════════════════════════ */

const API_BASE = '';
let currentAudit = null;
let authToken = localStorage.getItem('token');
let currentUser = null;

// ── Sample Clinical Notes ─────────────────────────────────
const SAMPLES = {
    pass: {
        note: `Patient is a 45-year-old male presenting with chronic low back pain for 8 weeks. Pain radiates to the left leg with numbness and tingling. Patient has completed 10 sessions of physical therapy with minimal improvement. Tried ibuprofen 800mg TID for 4 weeks and cyclobenzaprine 10mg QHS for 3 weeks without significant relief. Patient reports progressive weakness in left foot (L5 distribution). Requesting MRI lumbar spine to evaluate for disc herniation or spinal stenosis.`,
        payer: 'Generic Insurance',
    },
    fail: {
        note: `Patient complains of back pain for 2 weeks. No prior treatment attempted. Wants an MRI. No medications tried.`,
        payer: 'Blue Cross Blue Shield',
    },
    redflag: {
        note: `Patient is a 52-year-old female with acute onset low back pain for 1 week. Presenting with saddle anesthesia and new-onset bladder dysfunction. Unable to control urination since yesterday. Progressive bilateral leg weakness noted on exam. Urgent MRI lumbar spine requested to rule out cauda equina syndrome.`,
        payer: 'Aetna',
    },
};

// ── Init ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
    // ── High-End VFX Boot Sequencer ──
    const bootSequencePlayed = sessionStorage.getItem('bootSequencePlayed');
    const bSeq = document.getElementById('vfx-boot-sequence');
    const bFlash = document.getElementById('vfx-flash');
    
    if (bootSequencePlayed || !bSeq) {
        // Skip VFX if already booted this session
        document.body.classList.remove('booting');
        if (bSeq) bSeq.remove();
        if (bFlash) bFlash.remove();
        const bNamaste = document.getElementById('vfx-namaste-screen');
        if (bNamaste) bNamaste.remove();
    } else {
        // ── PHASE 1: Quantum Matrix Tunnel (0s - 3.5s) ──
        initBootSparks();
        const bNamaste = document.getElementById('vfx-namaste-screen');

        // ── PHASE 2: Namaste Screen Transition (3.5s) ──
        setTimeout(() => {
            if (bSeq) bSeq.style.opacity = '0';
            if (bNamaste) bNamaste.classList.add('active');
        }, 3500);

        // ── PHASE 3: Flash Transition (8.5s) ──
        setTimeout(() => {
            if (bFlash) bFlash.classList.add('flash-active');
        }, 8500);

        // ── PHASE 4: UI Drop-in (8.7s) ──
        setTimeout(() => {
            document.body.classList.remove('booting');
            if (bNamaste) bNamaste.style.opacity = '0';
        }, 8700);

        // ── PHASE 5: Cleanup (10.0s) ──
        setTimeout(() => {
            if (bSeq) bSeq.remove();
            if (bFlash) bFlash.remove();
            if (bNamaste) bNamaste.remove();
            sessionStorage.setItem('bootSequencePlayed', 'true');
        }, 10000);
    }
    addSVGGradient();
    initScrollEffects();
    initParticles();
    initPremiumVFX();

    // Check Auth State
    if (authToken) {
        try {
            const resp = await fetch(`${API_BASE}/api/auth/me`, {
                headers: { 'X-Auth-Token': authToken }
            });
            if (resp.ok) {
                currentUser = await resp.json();
                routeToRole(currentUser.role);
                console.log('[Auth] Restored session for', currentUser.role);
            } else {
                logout();
            }
        } catch {
            logout();
        }
    } else {
        switchView('landing');
    }
});

// ── Scroll Effects ────────────────────────────────────────
function initScrollEffects() {
    const header = document.getElementById('app-header');
    let ticking = false;

    window.addEventListener('scroll', () => {
        if (!ticking) {
            requestAnimationFrame(() => {
                if (window.scrollY > 20) {
                    header.classList.add('scrolled');
                } else {
                    header.classList.remove('scrolled');
                }
                ticking = false;
            });
            ticking = true;
        }
    });
}

// ── View Switching ────────────────────────────────────────
function switchView(viewName) {
    document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active-view'));
    const target = document.getElementById('view-' + viewName);
    if (target) target.classList.add('active-view');
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function routeToRole(role) {
    // Show portal welcome splash page first
    const name = currentUser.full_name || currentUser.username;
    if (role === 'doctor') {
        document.getElementById('pw-doctor-name').textContent = name;
    } else if (role === 'insurer') {
        document.getElementById('pw-insurer-name').textContent = name;
    } else if (role === 'patient') {
        document.getElementById('pw-patient-name').textContent = name;
    }
    switchView(role + '-welcome');
}

function enterPortal(role) {
    switchView(role);
    if (role === 'doctor') {
        document.getElementById('doc-welcome-name').textContent = currentUser.full_name || currentUser.username;
        loadPayers();
        fetchDoctorReports();
    } else if (role === 'patient') {
        document.getElementById('pat-welcome-name').textContent = currentUser.full_name || currentUser.username;
        document.getElementById('pat-code-display').textContent = currentUser.patient_code || 'Pending';
        fetchPatientReports();
    }
    // Insurer view doesn't need pre-loading — driven by search
}

// ── Doctor Welcome: Go back & reset ──────────────────────
function goToDoctorWelcome() {
    // Hide Done button for next time
    const doneBtn = document.getElementById('btn-done-next');
    if (doneBtn) doneBtn.classList.add('hidden');
    // Clear search results
    document.getElementById('doc-search-results').classList.add('hidden');
    document.getElementById('doc-search-input').value = '';
    // Navigate back to doctor welcome splash
    switchView('doctor-welcome');
}

// ── Doctor: Search Patient History ───────────────────────
async function doctorSearchPatient() {
    const code = document.getElementById('doc-search-input').value.trim();
    if (!code) { showToast('⚠️ Please enter a Patient Code'); return; }

    try {
        const resp = await fetch(`${API_BASE}/api/insurer/reports/search?patient_code=${encodeURIComponent(code)}`, {
            headers: { 'X-Auth-Token': authToken }
        });
        const data = await resp.json();

        if (!data.success) {
            showToast(`❌ ${data.error || 'Patient not found'}`);
            document.getElementById('doc-search-results').classList.add('hidden');
            return;
        }

        // Show results
        const container = document.getElementById('doc-search-results');
        container.classList.remove('hidden');
        document.getElementById('doc-search-patient-name').textContent = data.patient_name || 'Unknown';
        document.getElementById('doc-search-patient-code').textContent = `(${code})`;

        const list = document.getElementById('doc-search-reports-list');
        if (data.reports.length === 0) {
            list.innerHTML = `<div style="text-align:center; padding:2rem; color:var(--text-muted);">No reports found for this patient.</div>`;
        } else {
            list.innerHTML = data.reports.map(r => `
                <div class="glass-card" style="margin-bottom: 1rem;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 12px;">
                        <div style="font-family:'Outfit',sans-serif; font-weight:700; color:var(--text-white);">
                            📋 Report #${r.id}
                            <span style="font-size:0.78rem; color:var(--text-dim); margin-left:8px;">${r.submitted_at || ''}</span>
                        </div>
                    </div>
                    <div style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:10px;">
                        <strong>Payer:</strong> ${r.payer || 'N/A'}
                        ${r.requested_procedure ? ` · <strong>Procedure:</strong> ${r.requested_procedure}` : ''}
                    </div>
                    <div style="background:rgba(10,15,30,0.7); border:1px solid var(--border-dim); border-radius:var(--radius-sm); padding:14px; font-family:'JetBrains Mono',monospace; font-size:0.8rem; color:var(--text-primary); max-height:120px; overflow-y:auto; white-space:pre-wrap;">${r.clinical_note || ''}</div>
                    <div style="margin-top:12px;">
                        <button class="btn btn-primary" onclick="runAdjudicationFromSearch(${r.id}, '${escapeAttr(r.clinical_note || '')}', '${escapeAttr(r.payer || '')}', '${escapeAttr(r.requested_procedure || '')}')">⚡ Run AI Adjudication</button>
                    </div>
                </div>
            `).join('');
        }

        showToast(`✅ Found ${data.reports.length} report(s) for ${data.patient_name}`);
    } catch (err) {
        showToast(`❌ Search failed: ${err.message}`);
    }
}

// ── Doctor: Run adjudication from search results ─────────
function runAdjudicationFromSearch(reportId, clinicalNote, payer, procedure) {
    runAdjudication(reportId, clinicalNote);
}

// ── Auth Logic ────────────────────────────────────────────
async function handleAuth(endpoint, payload) {
    try {
        const resp = await fetch(`${API_BASE}/api/auth/${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await resp.json();
        if (data.success) {
            authToken = data.token;
            localStorage.setItem('token', authToken);
            currentUser = { role: data.role, patient_code: data.patient_code, full_name: payload.full_name || payload.username, username: payload.username };
            routeToRole(data.role);
            showToast('✅ Signed in successfully!');
        } else {
            showToast(`❌ ${data.error}`);
        }
    } catch (err) {
        showToast('❌ Connection error — is the server running?');
    }
}

function handleLogin(role) {
    let payload = { role, password: 'abc' };
    if (role === 'doctor') {
        payload.username = document.getElementById('doc-license').value;
        payload.password = document.getElementById('doc-name').value;
    } else if (role === 'insurer') {
        payload.username = document.getElementById('ins-company').value;
        payload.password = document.getElementById('ins-pass').value;
    } else if (role === 'patient') {
        payload.username = document.getElementById('pat-mobile').value;
        payload.password = payload.username;
    }

    if (!payload.username) { showToast('⚠️ Please fill in all required fields'); return; }
    handleAuth('login', payload);
}

function handleRegister(role) {
    let payload = { role, password: 'abc' };
    if (role === 'doctor') {
        payload.username = document.getElementById('doc-license').value;
        payload.password = document.getElementById('doc-name').value;
        payload.full_name = payload.password;
    } else if (role === 'insurer') {
        payload.username = document.getElementById('ins-company').value;
        payload.password = document.getElementById('ins-pass').value;
        payload.full_name = payload.username;
    } else if (role === 'patient') {
        payload.username = document.getElementById('pat-mobile').value;
        payload.password = payload.username;
        payload.full_name = "Patient " + payload.username;
    }

    if (!payload.username) { showToast('⚠️ Please fill in all required fields'); return; }
    handleAuth('register', payload);
}

function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('token');
    switchView('landing');
    showToast('👋 Signed out');
}

async function loadPayers() {
    try {
        const resp = await fetch(`${API_BASE}/api/payers`);
        const data = await resp.json();
        const select = document.getElementById('payer-select');
        select.innerHTML = data.payers
            .map((p, i) => `<option value="${p}" ${i === 0 ? 'selected' : ''}>${p}</option>`)
            .join('');
    } catch {
        document.getElementById('payer-select').innerHTML =
            `<option value="Generic Insurance">Generic Insurance</option>`;
    }
}

function addSVGGradient() {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', '0');
    svg.setAttribute('height', '0');
    svg.style.position = 'absolute';
    svg.innerHTML = `<defs><linearGradient id="score-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#6366f1"/><stop offset="50%" stop-color="#06b6d4"/><stop offset="100%" stop-color="#10b981"/>
    </linearGradient></defs>`;
    document.body.appendChild(svg);
}

function loadSample(type) {
    const s = SAMPLES[type];
    document.getElementById('clinical-note').value = s.note.trim();
    const select = document.getElementById('payer-select');
    for (let opt of select.options) {
        if (opt.value === s.payer) { opt.selected = true; break; }
    }
    document.getElementById('procedure-input').value = '';

    const labels = { pass: '✅ Strong case', fail: '⚠️ Weak case', redflag: '🚩 Red flag case' };
    showToast(`${labels[type]} loaded`);
}


// ══════════════════════════════════════════════════════════
// DOCTOR PORTAL
// ══════════════════════════════════════════════════════════

// ── Submit Report (saves to DB only, no AI) ───────────────
async function submitReport() {
    const patName = document.getElementById('patient-name').value.trim();
    const patMobile = document.getElementById('patient-mobile').value.trim();
    const note = document.getElementById('clinical-note').value.trim();
    const payer = document.getElementById('payer-select').value;
    const procedure = document.getElementById('procedure-input').value.trim();

    if (!patMobile || !patName) { showToast('⚠️ Patient Name and Mobile required'); return; }
    if (!note) { showToast('⚠️ Please enter a clinical note'); return; }
    if (!payer) { showToast('⚠️ Please select a payer'); return; }

    const btn = document.getElementById('btn-submit-report');
    btn.classList.add('loading');
    btn.disabled = true;

    try {
        const body = {
            patient_name: patName,
            patient_mobile: patMobile,
            clinical_note: note,
            payer
        };
        if (procedure) body.requested_procedure = procedure;

        const resp = await fetch(`${API_BASE}/api/doctor/report`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Auth-Token': authToken
            },
            body: JSON.stringify(body),
        });

        const data = await resp.json();

        if (!data.success) {
            showToast(`❌ ${data.error}`);
            return;
        }

        showToast(`✅ Report submitted! Patient Code: ${data.patient_code}`);

        // Clear form
        document.getElementById('patient-name').value = '';
        document.getElementById('patient-mobile').value = '';
        document.getElementById('clinical-note').value = '';
        document.getElementById('procedure-input').value = '';

        // Show "Done" button
        const doneBtn = document.getElementById('btn-done-next');
        if (doneBtn) doneBtn.classList.remove('hidden');

        // Refresh doctor's report list
        fetchDoctorReports();

    } catch (err) {
        showToast(`❌ Request failed: ${err.message}`);
    } finally {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
}

// ── Fetch Doctor's Own Reports ────────────────────────────
async function fetchDoctorReports() {
    try {
        const resp = await fetch(`${API_BASE}/api/doctor/reports`, {
            headers: { 'X-Auth-Token': authToken }
        });
        const data = await resp.json();
        const list = document.getElementById('doctor-reports-list');

        if (data.reports.length === 0) {
            list.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--text-muted);">
                    <div style="font-size: 2.5rem; margin-bottom: 12px;">📁</div>
                    <p style="font-size: 1rem; font-weight: 500;">No reports submitted yet</p>
                    <p style="font-size: 0.85rem; margin-top: 6px;">Fill in the form above and click "Submit Report" to get started.</p>
                </div>
            `;
            return;
        }

        list.innerHTML = data.reports.map(r => `
            <div class="report-card glass-card" style="border-left: 4px solid ${getStatusColor(r.decision_status)}; margin-bottom: 1rem;">
                <div class="report-card-header">
                    <strong>${r.procedure || 'General Evaluation'}</strong>
                    <span class="report-date">${new Date(r.created_at).toLocaleString()}</span>
                </div>
                <div><strong>Patient:</strong> ${r.patient_name} <span style="color: var(--text-dim); font-size: 0.85rem;">(${r.patient_code})</span></div>
                <div><strong>Payer:</strong> ${r.payer}</div>
                <div><strong>Status:</strong>
                    <span class="report-status-badge ${getStatusClass(r.decision_status)}">
                        ${r.decision_status}${r.readiness_score != null ? ` (${r.readiness_score}/100)` : ''}
                    </span>
                </div>
                <div style="margin-top: 0.75rem; font-size: 0.85rem; padding-top: 0.75rem; border-top: 1px dashed var(--border-dim); color: var(--text-secondary);">
                    <em>"${r.clinical_note.substring(0, 150)}${r.clinical_note.length > 150 ? '...' : ''}"</em>
                </div>
                <div style="margin-top: 1rem;">
                    <button class="btn btn-primary" style="width: 100%; display: flex; justify-content: center; align-items: center; gap: 8px;" onclick="runAdjudication(${r.id}, '${escapeHtml(r.clinical_note)}')">
                        ⚡ Run Pre-Adjudication
                    </button>
                </div>
            </div>
        `).join('');
    } catch {
        showToast('❌ Failed to load your reports');
    }
}


// ══════════════════════════════════════════════════════════
// INSURER PORTAL
// ══════════════════════════════════════════════════════════

async function searchInsurerReports() {
    const code = document.getElementById('search-pat-code').value.trim();
    if (!code) { showToast('⚠️ Enter a patient code to search'); return; }

    try {
        const resp = await fetch(`${API_BASE}/api/insurer/reports/search?patient_code=${encodeURIComponent(code)}`, {
            headers: { 'X-Auth-Token': authToken }
        });

        if (!resp.ok) {
            showToast('❌ Patient code not found');
            return;
        }

        const data = await resp.json();
        document.getElementById('insurer-results-container').classList.remove('hidden');
        document.getElementById('ins-search-name').textContent = data.patient_name;
        document.getElementById('ins-search-code').textContent = `(${data.patient_code})`;

        const list = document.getElementById('insurer-reports-list');
        if (data.reports.length === 0) {
            list.innerHTML = `
                <div class="glass-card" style="text-align: center; padding: 40px; color: var(--text-muted);">
                    <p>No reports filed for this patient.</p>
                </div>
            `;
            return;
        }

        list.innerHTML = data.reports.map(r => `
            <div class="report-card glass-card" style="border-left: 4px solid ${getStatusColor(r.decision_status)}; margin-bottom: 1rem;">
                <div class="report-card-header">
                    <strong>${r.procedure || 'General Evaluation'}</strong>
                    <span class="report-date">${new Date(r.created_at).toLocaleString()}</span>
                </div>
                <div><strong>Doctor:</strong> ${r.doctor_name}</div>
                <div><strong>Payer:</strong> ${r.payer}</div>
                <div><strong>Status:</strong>
                    <span class="report-status-badge ${getStatusClass(r.decision_status)}">
                        ${r.decision_status}${r.readiness_score != null ? ` (${r.readiness_score}/100)` : ''}
                    </span>
                </div>
                <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px dashed var(--border-dim);">
                    <div style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-dim); margin-bottom: 8px;">📜 Full Clinical Note / Prescription</div>
                    <div style="background: rgba(10, 15, 30, 0.6); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); padding: 14px; font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: var(--text-primary); line-height: 1.55; white-space: pre-wrap; max-height: 200px; overflow-y: auto;">${escapeHtml(r.clinical_note)}</div>
                </div>
                <div style="margin-top: 1rem;">
                    <button class="btn btn-primary" style="width: 100%; display: flex; justify-content: center; align-items: center; gap: 8px;" onclick="runAdjudication(${r.id}, '${escapeAttr(r.clinical_note)}')">
                        ⚡ Run Pre-Adjudication
                    </button>
                </div>
            </div>
        `).join('');
    } catch {
        showToast('❌ Error searching claims');
    }
}


// ══════════════════════════════════════════════════════════
// PATIENT PORTAL
// ══════════════════════════════════════════════════════════

async function fetchPatientReports() {
    try {
        const resp = await fetch(`${API_BASE}/api/patient/reports`, {
            headers: { 'X-Auth-Token': authToken }
        });
        const data = await resp.json();
        const list = document.getElementById('patient-reports-list');

        if (data.reports.length === 0) {
            list.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--text-muted);">
                    <div style="font-size: 2.5rem; margin-bottom: 12px;">📋</div>
                    <p style="font-size: 1rem; font-weight: 500;">No reports found yet</p>
                    <p style="font-size: 0.85rem; margin-top: 6px;">Your doctor hasn't submitted any claims for you yet.</p>
                </div>
            `;
            return;
        }

        list.innerHTML = data.reports.map(r => `
            <div class="report-card glass-card" style="border-left: 4px solid ${getStatusColor(r.decision_status)}; margin-bottom: 1rem;">
                <div class="report-card-header">
                    <strong>${r.procedure || 'General Evaluation'}</strong>
                    <span class="report-date">${new Date(r.created_at).toLocaleString()}</span>
                </div>
                <div><strong>Doctor:</strong> ${r.doctor_name}</div>
                <div><strong>Payer:</strong> ${r.payer}</div>
                <div><strong>Status:</strong>
                    <span class="report-status-badge ${getStatusClass(r.decision_status)}">
                        ${r.decision_status}${r.readiness_score != null ? ` (${r.readiness_score}/100)` : ''}
                    </span>
                </div>
                <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px dashed var(--border-dim);">
                    <div style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-dim); margin-bottom: 8px;">📜 Full Clinical Note / Prescription</div>
                    <div style="background: rgba(10, 15, 30, 0.6); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); padding: 14px; font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: var(--text-primary); line-height: 1.55; white-space: pre-wrap; max-height: 200px; overflow-y: auto;">${escapeHtml(r.clinical_note)}</div>
                </div>
                <div style="margin-top: 1rem;">
                    <button class="btn btn-primary" style="width: 100%; display: flex; justify-content: center; align-items: center; gap: 8px;" onclick="runAdjudication(${r.id}, '${escapeAttr(r.clinical_note)}')">
                        ⚡ Run Pre-Adjudication
                    </button>
                </div>
            </div>
        `).join('');
    } catch {
        showToast('❌ Failed to load patient history');
    }
}


// ══════════════════════════════════════════════════════════
// SHARED: RUN PRE-ADJUDICATION (all roles)
// ══════════════════════════════════════════════════════════

async function runAdjudication(reportId, clinicalNote) {
    showToast('⏳ Running AI pre-adjudication...');

    try {
        const resp = await fetch(`${API_BASE}/api/run-adjudication`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Auth-Token': authToken
            },
            body: JSON.stringify({ report_id: reportId }),
        });

        const data = await resp.json();

        if (!data.success) {
            showToast(`❌ ${data.error}`);
            return;
        }

        // Show patient code banner only for doctors
        if (currentUser.role === 'doctor' && data.patient_code) {
            document.getElementById('patient-code-alert').style.display = 'block';
            document.getElementById('doc-patient-code-display').textContent = data.patient_code;
        } else {
            document.getElementById('patient-code-alert').style.display = 'none';
        }

        currentAudit = data.audit_trace;
        document.getElementById('result-clinical-note').textContent = clinicalNote;
        switchView('result');
        renderResults(data.audit_trace);

    } catch (err) {
        showToast(`❌ Request failed: ${err.message}`);
    }
}

function goBackToDashboard() {
    if (!currentUser) { switchView('login'); return; }
    if (currentUser.role === 'insurer') {
        switchView('insurer');
    } else if (currentUser.role === 'patient') {
        switchView('patient');
        fetchPatientReports(); // Refresh to show updated status
    } else {
        switchView('doctor');
        fetchDoctorReports(); // Refresh to show updated status
    }
}


// ══════════════════════════════════════════════════════════
// RENDER RESULTS
// ══════════════════════════════════════════════════════════

function renderResults(audit) {
    renderDecision(audit);
    renderExtraction(audit.extraction);
    renderCodes(audit.code_mapping);
    renderPolicy(audit.policy_evaluation);
    renderDenials(audit.denial_simulation);
    renderRemediation(audit.remediation);
    renderRedTeam(audit.red_team_report);
    renderAuditJSON(audit);
    renderGraph(audit.evidence_graph);
}

function renderDecision(audit) {
    const d = audit.decision;
    const badge = document.getElementById('decision-badge');
    badge.textContent = d.status;
    badge.className = `decision-badge ${d.status}`;
    document.getElementById('decision-summary').textContent = d.summary;

    // Score ring
    const circumference = 2 * Math.PI * 52;
    const offset = circumference - (d.readiness_score / 100) * circumference;
    document.getElementById('score-ring-fill').style.strokeDashoffset = offset;
    animateNumber('score-value', d.readiness_score);

    // Meta
    document.getElementById('meta-policy').textContent = audit.policy_evaluation.policy_id;
    document.getElementById('meta-payer').textContent = audit.policy_evaluation.payer;
    const prob = audit.denial_simulation.estimated_denial_probability;
    document.getElementById('meta-denial-prob').textContent = `${(prob * 100).toFixed(0)}%`;
    document.getElementById('meta-denial-prob').style.color =
        prob > 0.5 ? '#ef4444' : prob > 0.2 ? '#f59e0b' : '#10b981';
}

function animateNumber(id, target) {
    const el = document.getElementById(id);
    let current = 0;
    const duration = 1200;
    const start = performance.now();

    function update(now) {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        current = Math.round(eased * target);
        el.textContent = current;
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

function renderExtraction(ext) {
    const grid = document.getElementById('extraction-grid');
    const items = [
        { label: 'Symptoms', value: ext.symptoms, tagClass: 'tag-blue' },
        { label: 'Duration', value: ext.duration_weeks !== null ? `${ext.duration_weeks} weeks` : 'Not documented', single: true },
        { label: 'PT Sessions', value: ext.pt_sessions !== null ? `${ext.pt_sessions} sessions` : 'Not documented', single: true },
        { label: 'Medications', value: ext.medications, tagClass: 'tag-cyan' },
        { label: 'Treatments Tried', value: ext.treatments_tried, tagClass: 'tag-green' },
        { label: 'Red Flags', value: ext.red_flags, tagClass: 'tag-red' },
        { label: 'Requested Procedure', value: ext.requested_procedure || 'Not specified', single: true },
    ];

    grid.innerHTML = items.map((item, i) => {
        let valueHTML;
        if (item.single) {
            valueHTML = `<div class="ei-value">${item.value}</div>`;
        } else if (Array.isArray(item.value) && item.value.length > 0) {
            valueHTML = `<div class="ei-value">${item.value.map(v => `<span class="tag ${item.tagClass}">${v}</span>`).join('')}</div>`;
        } else {
            valueHTML = `<div class="ei-value" style="color: var(--text-dim)">None found</div>`;
        }
        return `<div class="extraction-item" style="animation: fadeSlideUp 0.4s ${i * 0.05}s both var(--ease-out, cubic-bezier(0.16, 1, 0.3, 1))"><div class="ei-label">${item.label}</div>${valueHTML}</div>`;
    }).join('');
}

function renderCodes(codes) {
    document.getElementById('codes-display').innerHTML = `
        <div class="code-card">
            <div class="cc-system">ICD-10 Diagnosis</div>
            <div class="cc-code">${codes.icd10_code}</div>
            <div class="cc-desc">${codes.icd10_description}</div>
            <div class="cc-method">Method: ${codes.mapping_method}</div>
        </div>
        <div class="code-card">
            <div class="cc-system">CPT Procedure</div>
            <div class="cc-code">${codes.cpt_code}</div>
            <div class="cc-desc">${codes.cpt_description}</div>
            <div class="cc-method">Method: ${codes.mapping_method}</div>
        </div>`;
}

function renderPolicy(policy) {
    const container = document.getElementById('policy-rules');
    container.innerHTML = policy.rule_results.map((r, i) => `
        <div class="rule-item" style="animation: fadeSlideUp 0.4s ${i * 0.06}s both">
            <div class="rule-icon">${r.passed ? '✅' : '❌'}</div>
            <div class="rule-content">
                <div class="rc-id">${r.rule_id} · ${r.rule_type}</div>
                <div class="rc-desc">${r.description}</div>
                <div class="rc-detail">${r.detail}</div>
                ${r.required_value ? `<div class="rule-values">
                    <span class="rv-required">Required: ${r.required_value}</span>
                    <span class="rv-actual">Actual: ${r.actual_value}</span>
                </div>` : ''}
            </div>
        </div>`).join('');
}

function renderDenials(denial) {
    const container = document.getElementById('denial-results');
    const probColor = denial.estimated_denial_probability > 0.5 ? 'var(--red)' :
        denial.estimated_denial_probability > 0.2 ? 'var(--amber)' : 'var(--emerald)';

    let html = `<div class="denial-header">
        <div class="dh-stat"><div class="dh-label">Denial Likely</div>
            <div class="dh-value" style="color: ${denial.denial_likely ? 'var(--red)' : 'var(--emerald-light)'}">
                ${denial.denial_likely ? 'YES' : 'NO'}</div></div>
        <div class="dh-stat"><div class="dh-label">Probability</div>
            <div class="dh-value" style="color: ${probColor}">${(denial.estimated_denial_probability * 100).toFixed(0)}%</div></div>
        <div class="dh-stat"><div class="dh-label">Reasons</div>
            <div class="dh-value">${denial.denial_reasons.length}</div></div>
    </div>`;

    if (denial.denial_reasons.length === 0) {
        html += `<div class="no-denials">✅ No denial triggers identified — low risk of rejection</div>`;
    } else {
        html += denial.denial_reasons.map((r, i) => `
            <div class="denial-reason" style="animation: fadeSlideUp 0.4s ${i * 0.06}s both">
                <div class="dr-header">
                    <span class="dr-code">${r.code}</span>
                    <span class="dr-category">${r.category}</span>
                    <span class="dr-severity severity-${r.severity}">${r.severity}</span>
                </div>
                <div class="dr-text">${r.reason}</div>
                <div class="dr-payer">"${r.payer_language}"</div>
            </div>`).join('');
    }
    container.innerHTML = html;
}

function renderRemediation(rem) {
    const container = document.getElementById('remediation-plan');
    if (rem.actions.length === 0) {
        container.innerHTML = `<div class="no-denials">✅ No remediation needed — case meets all requirements</div>`;
        return;
    }

    let html = rem.actions.map((a, i) => `
        <div class="remediation-item" style="animation: fadeSlideUp 0.4s ${i * 0.06}s both">
            <div class="ri-header">
                <span class="ri-priority">P${a.priority}</span>
                <span class="ri-category">${a.category}</span>
            </div>
            <div class="ri-action">${a.action}</div>
            <div class="ri-meta">
                <span>Impact: ${a.impact}</span>
                ${a.estimated_time ? `<span>Time: ${a.estimated_time}</span>` : ''}
            </div>
        </div>`).join('');

    html += `<div class="remediation-footer">
        📈 Estimated score after remediation: <strong>${rem.estimated_score_after_remediation}/100</strong>
    </div>`;
    container.innerHTML = html;
}

function renderRedTeam(rt) {
    const container = document.getElementById('redteam-results');
    if (rt.challenges.length === 0) {
        container.innerHTML = `<div class="no-denials">🛡️ No adversarial challenges identified</div>`;
        return;
    }

    let html = rt.challenges.map((c, i) => `
        <div class="redteam-item" style="animation: fadeSlideUp 0.4s ${i * 0.06}s both">
            <span class="rt-severity severity-${c.severity}">${c.severity}</span>
            <div class="rt-challenge">${c.challenge}</div>
            <div class="rt-recommendation">💡 ${c.recommendation}</div>
        </div>`).join('');

    const riskColor = rt.overall_risk === 'high' ? 'var(--red)' :
        rt.overall_risk === 'medium' ? 'var(--amber)' : 'var(--emerald)';
    html += `<div class="redteam-footer" style="color: ${riskColor}; background: ${riskColor}12; border: 1px solid ${riskColor}25">
        Overall Adversarial Risk: ${rt.overall_risk.toUpperCase()}
    </div>`;
    container.innerHTML = html;
}

function renderAuditJSON(audit) {
    document.getElementById('audit-json').textContent = JSON.stringify(audit, null, 2);
}

// ── Evidence Graph (3D) ──────────────────────────────
let activeGraph3D = null;

function renderGraph(graph) {
    const container = document.getElementById('graph-container');
    container.innerHTML = '';

    if (activeGraph3D) {
        activeGraph3D._destructor();
        activeGraph3D = null;
    }

    if (!graph || !graph.nodes || graph.nodes.length === 0) return;

    const nodeColors = { fact: '#6366f1', code: '#06b6d4', policy_clause: '#10b981', violation: '#ef4444' };
    const linkColors = { supports: '#10b981', violates: '#ef4444', missing: '#f59e0b' };

    const gData = {
        nodes: graph.nodes.map(n => ({
            id: n.id,
            name: n.label,
            type: n.node_type,
            val: n.node_type === 'violation' ? 2 : 1
        })),
        links: graph.edges.map(e => ({
            source: e.source,
            target: e.target,
            relation: e.relation
        }))
    };

    const width = container.offsetWidth || window.innerWidth * 0.7;
    const height = 450;

    activeGraph3D = ForceGraph3D()(container)
        .width(width)
        .height(height)
        .backgroundColor('#0a0f1e')
        .graphData(gData)
        .nodeLabel('name')
        .nodeColor(node => nodeColors[node.type] || '#ffffff')
        .nodeResolution(16)
        .nodeOpacity(0.95)
        .linkColor(link => linkColors[link.relation] || '#ffffff')
        .linkWidth(2)
        .linkOpacity(0.6)
        .linkDirectionalParticles(2)
        .linkDirectionalParticleWidth(2.5)
        .linkDirectionalParticleSpeed(0.004)
        .onNodeClick(node => {
            const distance = 40;
            const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);
            activeGraph3D.cameraPosition(
                { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
                node,
                3000
            );
        });

    // Legend overlay
    const legend = document.createElement('div');
    legend.style.cssText = `
        position: absolute; top: 14px; left: 14px; color: white;
        background: rgba(6,8,15,0.75); backdrop-filter: blur(10px);
        padding: 14px 18px; border-radius: 10px;
        font-family: 'Outfit', sans-serif; font-size: 0.78rem;
        pointer-events: none; border: 1px solid rgba(99,102,241,0.12);
        line-height: 1.8;
    `;
    legend.innerHTML = `
        <strong style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.1em; color: #94a3b8;">Node Types</strong><br>
        <span style="color:#6366f1">●</span> Fact
        <span style="color:#06b6d4; margin-left: 8px;">●</span> Code
        <span style="color:#10b981; margin-left: 8px;">●</span> Policy Rule
        <span style="color:#ef4444; margin-left: 8px;">●</span> Violation
    `;
    container.style.position = 'relative';
    container.appendChild(legend);
}

// ── Tabs ──────────────────────────────────────────────────
function switchTab(tab) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
    document.getElementById(`tab-${tab}`).classList.add('active');
}

// ── Audit Actions ─────────────────────────────────────────
function copyAudit() {
    if (!currentAudit) return;
    navigator.clipboard.writeText(JSON.stringify(currentAudit, null, 2));
    showToast('📋 Audit JSON copied to clipboard');
}

function downloadAudit() {
    if (!currentAudit) return;
    const blob = new Blob([JSON.stringify(currentAudit, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit_trace_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('💾 Audit JSON downloaded');
}

// ── Helpers ───────────────────────────────────────────────
function getStatusColor(status) {
    if (status === 'SUBMISSION_READY') return '#4ade80';
    if (status === 'SUBMITTED') return '#60a5fa';
    if (status === 'NEEDS_MORE_EVIDENCE' || status === 'NEEDS_REVIEW') return '#f59e0b';
    return '#f87171';
}

function getStatusClass(status) {
    if (status === 'SUBMISSION_READY') return 'status-approved';
    if (status === 'SUBMITTED') return 'status-pending';
    if (status === 'NEEDS_MORE_EVIDENCE' || status === 'NEEDS_REVIEW') return 'status-pending';
    return 'status-blocked';
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function escapeAttr(str) {
    return str.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/\n/g, '\\n').replace(/\r/g, '');
}

// ── Toast ─────────────────────────────────────────────────
function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3500);
}

// ── Floating Particles ───────────────────────────────────
function initParticles() {
    // If the tsParticles library wasn't loaded, return early.
    if (!window.tsParticles) return;
    
    // Check if the container exists
    if (!document.getElementById('landing-particles')) return;

    tsParticles.load("landing-particles", {
        fullScreen: { enable: false },
        fpsLimit: 60,
        interactivity: {
            events: {
                onHover: { enable: true, mode: "grab" },
                resize: true,
            },
            modes: {
                grab: { distance: 150, links: { opacity: 0.6 } }
            },
        },
        particles: {
            color: { value: ["#7c3aed", "#06b6d4", "#ec4899"] },
            links: {
                color: "#10b981", // Neural green links
                distance: 120,
                enable: true,
                opacity: 0.2,
                width: 1,
            },
            move: {
                direction: "none",
                enable: true,
                outModes: { default: "bounce" },
                random: true,
                speed: 0.8,
                straight: false,
            },
            number: { density: { enable: true, area: 800 }, value: 80 },
            opacity: { value: 0.6, animation: { enable: true, speed: 1, minimumValue: 0.2 } },
            shape: { type: "circle" },
            size: { value: { min: 1, max: 4 } },
        },
        detectRetina: true,
    });
}

// ── Ultra-Premium Web Effects ───────────────────────────
function initBootSparks() {
    const container = document.getElementById('vfx-sparks-container');
    if (!container) return;
    
    // Generate 40 neural sparks dynamically
    for (let i = 0; i < 40; i++) {
        const spark = document.createElement('div');
        spark.className = 'spark';
        
        // Random positioning in 3D polar coordinates
        const distance = Math.random() * 400 + 100;
        const angle = Math.random() * Math.PI * 2;
        const x = Math.cos(angle) * distance;
        const y = Math.sin(angle) * distance;
        
        spark.style.left = `calc(50% + ${x}px)`;
        spark.style.top = `calc(50% + ${y}px)`;
        spark.style.animationDelay = `${Math.random() * 3}s`;
        spark.style.opacity = Math.random();
        
        container.appendChild(spark);
    }
}

function initPremiumVFX() {
    // 1. Neon Spotlight tracking
    const spotlight = document.getElementById('neon-spotlight');
    if (spotlight) {
        document.addEventListener('mousemove', (e) => {
            requestAnimationFrame(() => {
                spotlight.style.transform = `translate(${e.clientX}px, ${e.clientY}px)`;
            });
        });
    }

    // 2. Magnetic 3D Tilt
    const tiltElements = document.querySelectorAll('.magnetic-tilt');
    tiltElements.forEach(el => {
        el.addEventListener('mousemove', (e) => {
            const rect = el.getBoundingClientRect();
            // Calculate cursor position inside the element (0 to 1)
            const x = (e.clientX - rect.left) / rect.width;
            const y = (e.clientY - rect.top) / rect.height;
            
            // Convert to a multiplier (-1 to 1)
            const multiplierX = (x - 0.5) * 2;
            const multiplierY = (y - 0.5) * 2;
            
            // Calculate degrees (max 15 degrees tilt)
            const rotateX = multiplierY * -15; // Y controls X rotation. Inverse so top tilts away
            const rotateY = multiplierX * 15;  // X controls Y rotation.
            
            requestAnimationFrame(() => {
                // Combine with existing translateZ if present for extra pop
                el.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
            });
        });

        el.addEventListener('mouseleave', () => {
            requestAnimationFrame(() => {
                el.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)`;
            });
        });
    });
}
