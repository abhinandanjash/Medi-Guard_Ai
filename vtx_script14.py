# vtx_script14.py - Inject new portal functions into app.js
with open("app/static/app.js", "r", encoding="utf-8", errors="replace") as f:
    content = f.read()

# --- Fix 1: Update routeToRole ---
OLD_ROUTE = "function routeToRole(role) {"
if OLD_ROUTE in content:
    start = content.index(OLD_ROUTE)
    # Find end of this function (closing brace at column 0)
    depth = 0
    i = start
    while i < len(content):
        if content[i] == '{': depth += 1
        elif content[i] == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
        i += 1
    NEW_ROUTE = """function routeToRole(role) {
    const name = currentUser.full_name || currentUser.username;
    if (role === 'doctor') {
        document.getElementById('pw-doctor-name').textContent = name;
        switchView('doctor-welcome');
    } else if (role === 'insurer') {
        document.getElementById('pw-insurer-name').textContent = name;
        switchView('insurer-welcome');
    } else if (role === 'patient') {
        document.getElementById('pw-patient-name').textContent = name;
        switchView('patient-welcome');
    } else if (role === 'hospital') {
        document.getElementById('hosp-org-display').textContent = currentUser.organization_name || '';
        document.getElementById('hosp-username-display').textContent = currentUser.username || '';
        switchView('hospital');
    } else if (role === 'pharma') {
        document.getElementById('pharma-org-display').textContent = currentUser.organization_name || '';
        document.getElementById('pharma-username-display').textContent = currentUser.username || '';
        switchView('pharma');
    } else {
        switchView(role + '-welcome');
    }
}"""
    content = content[:start] + NEW_ROUTE + content[end:]
    print("routeToRole updated")

# --- Fix 2: Update enterPortal ---
OLD_ENTER = "function enterPortal(role) {"
if OLD_ENTER in content:
    start = content.index(OLD_ENTER)
    depth = 0
    i = start
    while i < len(content):
        if content[i] == '{': depth += 1
        elif content[i] == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
        i += 1
    NEW_ENTER = """function enterPortal(role) {
    switchView(role);
    if (role === 'doctor') {
        document.getElementById('doc-welcome-name').textContent = currentUser.full_name || currentUser.username;
        loadPayers();
        fetchDoctorReports();
        fetchDoctorSummaries();
    } else if (role === 'patient') {
        document.getElementById('pat-welcome-name').textContent = currentUser.full_name || currentUser.username;
        document.getElementById('pat-code-display').textContent = currentUser.patient_code || 'Pending';
        fetchPatientReports();
        fetchPatientSubmissions();
        checkPatientHistoryPrompt();
    }
}"""
    content = content[:start] + NEW_ENTER + content[end:]
    print("enterPortal updated")

# --- Fix 3: Store organization_name in currentUser ---
OLD_CU = "currentUser = { role: data.role, patient_code: data.patient_code, full_name: payload.full_name || payload.username, username: payload.username };"
NEW_CU = "currentUser = { role: data.role, patient_code: data.patient_code, full_name: payload.full_name || payload.username, username: payload.username, organization_name: data.organization_name };"
if OLD_CU in content:
    content = content.replace(OLD_CU, NEW_CU, 1)
    print("currentUser updated")

# --- Fix 4: Inject all new functions after logout() ---
LOGOUT_MARKER = "function logout() {"
if LOGOUT_MARKER in content:
    start = content.index(LOGOUT_MARKER)
    depth = 0
    i = start
    while i < len(content):
        if content[i] == '{': depth += 1
        elif content[i] == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
        i += 1

    NEW_FUNCTIONS = """
// ── Hospital Auth ─────────────────────────────────────────────

async function handleHospitalAuth(action) {
    const regNo = document.getElementById('hosp-reg-no').value.trim();
    const pass = document.getElementById('hosp-pass').value.trim();
    const orgName = document.getElementById('hosp-org-name').value.trim();
    const extra = document.getElementById('hosp-register-extra');
    if (action === 'register' && extra.style.display === 'none') { extra.style.display = 'block'; return; }
    if (!regNo || !pass) { showToast('⚠️ Enter Registration No. and Password'); return; }
    const payload = { username: regNo, password: pass, role: 'hospital', organization_name: orgName || regNo, full_name: orgName || regNo };
    try {
        const resp = await fetch(`${API_BASE}/api/auth/${action}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        const data = await resp.json();
        if (data.success) {
            authToken = data.token; localStorage.setItem('token', authToken);
            currentUser = { role: 'hospital', username: regNo, organization_name: data.organization_name || orgName };
            routeToRole('hospital'); showToast('✅ Hospital logged in!');
        } else { showToast(`❌ ${data.error}`); }
    } catch(e) { showToast('❌ Connection error'); }
}

async function handlePharmaAuth(action) {
    const license = document.getElementById('pharma-license').value.trim();
    const pass = document.getElementById('pharma-pass').value.trim();
    const orgName = document.getElementById('pharma-org-name').value.trim();
    const extra = document.getElementById('pharma-register-extra');
    if (action === 'register' && extra.style.display === 'none') { extra.style.display = 'block'; return; }
    if (!license || !pass) { showToast('⚠️ Enter Drug License No. and Password'); return; }
    const payload = { username: license, password: pass, role: 'pharma', organization_name: orgName || license, full_name: orgName || license };
    try {
        const resp = await fetch(`${API_BASE}/api/auth/${action}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        const data = await resp.json();
        if (data.success) {
            authToken = data.token; localStorage.setItem('token', authToken);
            currentUser = { role: 'pharma', username: license, organization_name: data.organization_name || orgName };
            routeToRole('pharma'); showToast('✅ Pharma portal logged in!');
        } else { showToast(`❌ ${data.error}`); }
    } catch(e) { showToast('❌ Connection error'); }
}

// ── Hospital Dashboard Functions ──────────────────────────────

async function hospitalLookupPatient() {
    const code = document.getElementById('hosp-patient-code').value.trim();
    if (!code) { showToast('⚠️ Enter a patient code'); return; }
    try {
        const resp = await fetch(`${API_BASE}/api/hospital/patient-history/${encodeURIComponent(code)}`, { headers: { 'X-Auth-Token': authToken } });
        const data = await resp.json();
        if (!data.success) { showToast('❌ Patient not found'); return; }
        document.getElementById('hosp-patient-info').style.display = 'block';
        document.getElementById('hosp-patient-name-display').textContent = data.patient_name || 'Unknown';
        document.getElementById('hosp-patient-code-display').textContent = data.patient_code;
        document.getElementById('hosp-submit-patient-code').value = data.patient_code;
        const h = data.history;
        const el = document.getElementById('hosp-medical-history-display');
        if (!h) { el.innerHTML = '<p style="color:var(--text-muted);">No medical history recorded yet.</p>'; return; }
        el.innerHTML = `<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;font-size:0.88rem;">
            <div><strong>Height/Weight:</strong> ${h.height_cm||'-'}cm / ${h.weight_kg||'-'}kg</div>
            <div><strong>Age/Blood:</strong> ${h.age||'-'}yrs / ${h.blood_group||'-'}</div>
            <div style="grid-column:1/-1;"><strong>Past History:</strong> ${h.past_medical_history||'None'}</div>
            <div style="grid-column:1/-1;"><strong>Genetic Diseases:</strong> ${h.genetic_diseases||'None'}</div>
            <div style="grid-column:1/-1;"><strong>Current Medications:</strong> ${h.current_medications||'None'}</div>
            <div style="grid-column:1/-1;"><strong>Allergies:</strong> ${h.allergies||'None'}</div>
            <div style="grid-column:1/-1;"><strong>Past Surgeries:</strong> ${h.past_surgeries||'None'}</div>
        </div>`;
        document.getElementById('hosp-summary-text').value =
            `Patient: ${data.patient_name} | Code: ${data.patient_code}\\nAge: ${h.age||'-'} | Blood: ${h.blood_group||'-'} | H: ${h.height_cm||'-'}cm | W: ${h.weight_kg||'-'}kg\\n\\nPAST HISTORY:\\n${h.past_medical_history||'None'}\\n\\nGENETIC DISEASES:\\n${h.genetic_diseases||'None'}\\n\\nMEDICATIONS:\\n${h.current_medications||'None'}\\n\\nALLERGIES:\\n${h.allergies||'None'}\\n\\nSURGERIES:\\n${h.past_surgeries||'None'}`;
        showToast('✅ Patient found');
    } catch(e) { showToast(`❌ ${e.message}`); }
}

async function hospitalOpenSummaryModal() {
    document.getElementById('hosp-summary-modal').style.display = 'flex';
    try {
        const resp = await fetch(`${API_BASE}/api/hospital/doctors`, { headers: { 'X-Auth-Token': authToken } });
        const data = await resp.json();
        document.getElementById('hosp-doctor-select').innerHTML = data.doctors.length === 0
            ? '<option>No doctors registered yet</option>'
            : data.doctors.map(d => `<option value="${d.id}">${d.full_name} (${d.license})</option>`).join('');
    } catch(e) { showToast('❌ Could not load doctors'); }
}

async function hospitalSendSummary() {
    const code = document.getElementById('hosp-patient-code-display').textContent.trim();
    const doctorId = document.getElementById('hosp-doctor-select').value;
    const summaryText = document.getElementById('hosp-summary-text').value.trim();
    if (!summaryText || !doctorId) { showToast('⚠️ Select a doctor and add summary'); return; }
    try {
        const resp = await fetch(`${API_BASE}/api/hospital/send-summary`, {
            method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Auth-Token': authToken },
            body: JSON.stringify({ patient_code: code, doctor_name: doctorId, summary_text: summaryText })
        });
        const data = await resp.json();
        if (data.success) { showToast('✅ Summary sent to doctor!'); document.getElementById('hosp-summary-modal').style.display = 'none'; }
        else { showToast(`❌ ${data.error}`); }
    } catch(e) { showToast(`❌ ${e.message}`); }
}

async function hospitalSubmit() {
    const patCode = document.getElementById('hosp-submit-patient-code').value.trim();
    const type = document.getElementById('hosp-submit-type').value;
    const title = document.getElementById('hosp-submit-title').value.trim();
    const desc = document.getElementById('hosp-submit-desc').value.trim();
    const amount = parseFloat(document.getElementById('hosp-submit-amount').value) || null;
    const admitted = document.getElementById('hosp-patient-admitted').value === 'true';
    if (!patCode || !title) { showToast('⚠️ Patient Code and Title required'); return; }
    try {
        const resp = await fetch(`${API_BASE}/api/hospital/submit`, {
            method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Auth-Token': authToken },
            body: JSON.stringify({ patient_code: patCode, submission_type: type, title, description: desc, amount, patient_admitted: admitted })
        });
        const data = await resp.json();
        if (data.success) {
            showToast(`✅ Submitted! ID: #${data.submission_id}`);
            ['hosp-submit-title','hosp-submit-desc','hosp-submit-amount'].forEach(id => { const el = document.getElementById(id); if(el) el.value=''; });
        } else { showToast(`❌ ${data.error}`); }
    } catch(e) { showToast(`❌ ${e.message}`); }
}

async function pharmaSubmit() {
    const patCode = document.getElementById('pharma-submit-patient-code').value.trim();
    const type = document.getElementById('pharma-submit-type').value;
    const title = document.getElementById('pharma-submit-title').value.trim();
    const desc = document.getElementById('pharma-submit-desc').value.trim();
    const amount = parseFloat(document.getElementById('pharma-submit-amount').value) || null;
    if (!patCode || !title) { showToast('⚠️ Patient Code and Title required'); return; }
    try {
        const resp = await fetch(`${API_BASE}/api/pharma/submit`, {
            method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Auth-Token': authToken },
            body: JSON.stringify({ patient_code: patCode, submission_type: type, title, description: desc, amount })
        });
        const data = await resp.json();
        if (data.success) {
            showToast(`✅ Submitted! ID: #${data.submission_id}`);
            ['pharma-submit-title','pharma-submit-desc','pharma-submit-amount'].forEach(id => { const el = document.getElementById(id); if(el) el.value=''; });
        } else { showToast(`❌ ${data.error}`); }
    } catch(e) { showToast(`❌ ${e.message}`); }
}

function toggleBillAmount(prefix) {
    const type = document.getElementById(`${prefix}-submit-type`).value;
    const group = document.getElementById(`${prefix}-amount-group`);
    if (group) group.style.display = type === 'bill' ? 'block' : 'none';
}

// ── Patient Medical History ────────────────────────────────────

async function checkPatientHistoryPrompt() {
    try {
        const resp = await fetch(`${API_BASE}/api/patient/medical-history`, { headers: { 'X-Auth-Token': authToken } });
        const data = await resp.json();
        if (data.success && !data.history) setTimeout(() => switchView('patient-history-form'), 800);
    } catch(e) {}
}

async function savePatientHistory() {
    const payload = {
        height_cm: parseFloat(document.getElementById('ph-height').value) || null,
        weight_kg: parseFloat(document.getElementById('ph-weight').value) || null,
        age: parseInt(document.getElementById('ph-age').value) || null,
        blood_group: document.getElementById('ph-blood').value || null,
        past_medical_history: document.getElementById('ph-past-history').value.trim() || null,
        genetic_diseases: document.getElementById('ph-genetic').value.trim() || null,
        current_medications: document.getElementById('ph-meds').value.trim() || null,
        allergies: document.getElementById('ph-allergies').value.trim() || null,
        past_surgeries: document.getElementById('ph-surgeries').value.trim() || null,
    };
    try {
        const resp = await fetch(`${API_BASE}/api/patient/medical-history`, {
            method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Auth-Token': authToken },
            body: JSON.stringify(payload)
        });
        const data = await resp.json();
        if (data.success) { showToast('✅ Medical profile saved!'); switchView('patient'); }
        else { showToast(`❌ ${data.error}`); }
    } catch(e) { showToast(`❌ ${e.message}`); }
}

async function fetchPatientSubmissions() {
    try {
        const resp = await fetch(`${API_BASE}/api/patient/submissions`, { headers: { 'X-Auth-Token': authToken } });
        const data = await resp.json();
        const el = document.getElementById('patient-submissions-list');
        if (!el) return;
        if (!data.submissions || data.submissions.length === 0) {
            el.innerHTML = '<div style="text-align:center;padding:2rem;color:var(--text-muted);">No hospital or pharmacy submissions yet.</div>'; return;
        }
        el.innerHTML = data.submissions.map(s => `
            <div class="glass-card" style="margin-bottom:1rem;border-left:4px solid ${s.submitter_role==='hospital'?'#10b981':'#6366f1'}">
                <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:0.5rem;">
                    <strong>${s.title} <span style="font-size:0.78rem;font-weight:400;color:var(--text-muted);">[${s.submission_type}]</span></strong>
                    <span style="font-size:0.78rem;color:var(--text-dim);">${s.submitter_role==='hospital'?'🏥':'💊'} ${s.submitter_name}</span>
                </div>
                ${s.description?`<div style="margin-top:0.4rem;font-size:0.84rem;color:var(--text-secondary);">${s.description}</div>`:''}
                ${s.amount?`<div style="margin-top:0.4rem;font-weight:700;color:#10b981;">₹ ${s.amount.toLocaleString('en-IN')}</div>`:''}
                <div style="font-size:0.75rem;color:var(--text-dim);margin-top:0.3rem;">${new Date(s.created_at).toLocaleString()}</div>
            </div>`).join('');
    } catch(e) {}
}

async function fetchDoctorSummaries() {
    try {
        const resp = await fetch(`${API_BASE}/api/doctor/summaries`, { headers: { 'X-Auth-Token': authToken } });
        const data = await resp.json();
        const el = document.getElementById('doctor-summaries-list');
        if (!el) return;
        if (!data.summaries || data.summaries.length === 0) {
            el.innerHTML = '<div style="text-align:center;padding:1.5rem;color:var(--text-muted);font-size:0.9rem;">No summaries received yet.</div>'; return;
        }
        el.innerHTML = data.summaries.map(s => `
            <div class="glass-card" style="margin-bottom:1rem;border-left:4px solid #10b981;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">
                    <strong>Patient: ${s.patient_name} <span style="color:var(--cyan);">(${s.patient_code})</span></strong>
                    <span style="font-size:0.78rem;color:var(--text-dim);">From: ${s.sent_by}</span>
                </div>
                <pre style="white-space:pre-wrap;font-family:'JetBrains Mono',monospace;font-size:0.78rem;color:var(--text-secondary);background:rgba(0,0,0,0.2);padding:1rem;border-radius:8px;max-height:200px;overflow-y:auto;">${s.summary_text}</pre>
                <div style="font-size:0.75rem;color:var(--text-dim);margin-top:0.4rem;">${new Date(s.created_at).toLocaleString()}</div>
            </div>`).join('');
    } catch(e) {}
}

"""
    content = content[:end] + NEW_FUNCTIONS + content[end:]
    print("All new functions injected after logout()")

with open("app/static/app.js", "w", encoding="utf-8") as f:
    f.write(content)

print("app.js written successfully")
