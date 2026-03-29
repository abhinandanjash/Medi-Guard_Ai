/* ═══════════════════════════════════════════════════════════
   Prior Auth Engine — Frontend Application
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
    addSVGGradient();
    
    // Bind buttons
    const evalBtn = document.getElementById('btn-evaluate');
    if (evalBtn) evalBtn.addEventListener('click', (e) => { e.preventDefault(); evaluate(); });

    document.getElementById('btn-sample-pass')?.addEventListener('click', () => loadSample('pass'));
    document.getElementById('btn-sample-fail')?.addEventListener('click', () => loadSample('fail'));
    document.getElementById('btn-sample-red')?.addEventListener('click', () => loadSample('redflag'));

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
        switchView('login');
    }
});

function switchView(viewName) {
    document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active-view'));
    document.getElementById('view-' + viewName).classList.add('active-view');
}

function routeToRole(role) {
    switchView(role);
    if (role === 'doctor') {
        document.getElementById('doc-welcome-name').textContent = currentUser.full_name || currentUser.username;
        loadPayers();
    } else if (role === 'patient') {
        document.getElementById('pat-welcome-name').textContent = currentUser.full_name || currentUser.username;
        document.getElementById('pat-code-display').textContent = currentUser.patient_code || 'Pending';
        fetchPatientReports();
    }
}

// ── Auth Logic ────────────────────────────────────────────
function switchLoginTab(role) {
    document.querySelectorAll('.login-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`.login-tab[onclick*="${role}"]`).classList.add('active');
    document.querySelectorAll('.login-form').forEach(f => f.classList.remove('active-form'));
    document.getElementById('login-' + role).classList.add('active-form');
}

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
            showToast(`Logged in successfully!`);
        } else {
            showToast(`Error: ${data.error}`);
        }
    } catch (err) {
        showToast('Connection error');
    }
}

function handleLogin(role) {
    let payload = { role, password: 'abc' }; // Simple password fallback for prototype
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
    
    if (!payload.username) { showToast('Please enter required fields'); return; }
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
    
    if (!payload.username) { showToast('Please enter required fields'); return; }
    handleAuth('register', payload);
}

function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('token');
    switchView('login');
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
    svg.innerHTML = `<defs><linearGradient id="score-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#6366f1"/><stop offset="100%" stop-color="#06b6d4"/>
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
    showToast(`Loaded ${type === 'pass' ? 'strong' : type === 'fail' ? 'weak' : 'red flag'} sample case`);
}

// ── Evaluate (Doctor) ─────────────────────────────────────
async function evaluate() {
    console.log('[Prior Auth] evaluate() called');
    const patName = document.getElementById('patient-name').value.trim();
    const patMobile = document.getElementById('patient-mobile').value.trim();
    const note = document.getElementById('clinical-note').value.trim();
    const payer = document.getElementById('payer-select').value;
    const procedure = document.getElementById('procedure-input').value.trim();

    if (!patMobile || !patName) { showToast('Patient Name and Mobile required'); return; }
    if (!note) { showToast('Please enter a clinical note'); return; }
    if (!payer) { showToast('Please select a payer'); return; }

    const btn = document.getElementById('btn-evaluate');
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
            showToast(`Error: ${data.error}`);
            return;
        }

        // Display the unique Patient Code given back by the server
        if (data.patient_code) {
            document.getElementById('patient-code-alert').style.display = 'block';
            document.getElementById('doc-patient-code-display').textContent = data.patient_code;
        }

        currentAudit = data.audit_trace;
        document.getElementById('results-container').classList.remove('hidden');
        renderResults(data.audit_trace);
        document.getElementById('results-container').scrollIntoView({ behavior: 'smooth', block: 'start' });

    } catch (err) {
        showToast(`Request failed: ${err.message}`);
    } finally {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
}

// ── Role Specific API Calls ───────────────────────────────
async function fetchPatientReports() {
    try {
        const resp = await fetch(`${API_BASE}/api/patient/reports`, {
            headers: { 'X-Auth-Token': authToken }
        });
        const data = await resp.json();
        const list = document.getElementById('patient-reports-list');
        
        if (data.reports.length === 0) {
            list.innerHTML = '<p style="color:var(--gray-400)">No reports found.</p>';
            return;
        }
        
        list.innerHTML = data.reports.map(r => `
            <div class="report-card">
                <div class="report-card-header">
                    <strong>Requested: ${r.procedure || 'General Evaluation'}</strong>
                    <span class="report-date">${new Date(r.created_at).toLocaleDateString()}</span>
                </div>
                <div><strong>Doctor:</strong> ${r.doctor_name}</div>
                <div><strong>Payer:</strong> ${r.payer}</div>
                <div><strong>Insurance Status:</strong> 
                    <span class="report-status-badge ${r.decision_status === 'SUBMISSION_READY' ? 'status-approved' : r.decision_status === 'NEEDS_REVIEW' ? 'status-pending' : 'status-blocked'}">
                        ${r.insurance_approval}
                    </span>
                </div>
            </div>
        `).join('');
    } catch {
        showToast('Failed to load patient history');
    }
}

async function searchInsurerReports() {
    const code = document.getElementById('search-pat-code').value.trim();
    if (!code) return;
    
    try {
        const resp = await fetch(`${API_BASE}/api/insurer/reports/search?patient_code=${encodeURIComponent(code)}`, {
            headers: { 'X-Auth-Token': authToken }
        });
        
        if (!resp.ok) {
            showToast('Patient code not found');
            return;
        }
        
        const data = await resp.json();
        document.getElementById('insurer-results-container').classList.remove('hidden');
        document.getElementById('ins-search-name').textContent = data.patient_name;
        
        const list = document.getElementById('insurer-reports-list');
        if (data.reports.length === 0) {
            list.innerHTML = '<p>No reports filed for this patient.</p>';
            return;
        }
        
        list.innerHTML = data.reports.map(r => `
            <div class="report-card" style="border-left: 4px solid ${r.decision_status === 'SUBMISSION_READY' ? '#4ade80' : '#f87171'}">
                <div class="report-card-header">
                    <strong>${r.procedure || 'Evaluation'} (Score: ${r.readiness_score}/100)</strong>
                    <span class="report-date">${new Date(r.created_at).toLocaleString()}</span>
                </div>
                <div><strong>Doctor:</strong> ${r.doctor_name}</div>
                <div><strong>AI Decision:</strong> ${r.decision_status}</div>
                <div style="margin-top: 0.5rem; font-size: 0.85rem; padding-top: 0.5rem; border-top: 1px dashed var(--border-light)">
                    <em>"${r.clinical_note.substring(0, 120)}..."</em>
                </div>
            </div>
        `).join('');
    } catch {
        showToast('Error searching claims');
    }
}

// ── Render ────────────────────────────────────────────────
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
    const step = Math.max(1, Math.floor(target / 40));
    const interval = setInterval(() => {
        current = Math.min(current + step, target);
        el.textContent = current;
        if (current >= target) clearInterval(interval);
    }, 25);
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

    grid.innerHTML = items.map(item => {
        let valueHTML;
        if (item.single) {
            valueHTML = `<div class="ei-value">${item.value}</div>`;
        } else if (Array.isArray(item.value) && item.value.length > 0) {
            valueHTML = `<div class="ei-value">${item.value.map(v => `<span class="tag ${item.tagClass}">${v}</span>`).join('')}</div>`;
        } else {
            valueHTML = `<div class="ei-value" style="color: var(--text-muted)">None found</div>`;
        }
        return `<div class="extraction-item"><div class="ei-label">${item.label}</div>${valueHTML}</div>`;
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
    container.innerHTML = policy.rule_results.map(r => `
        <div class="rule-item">
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
    const probColor = denial.estimated_denial_probability > 0.5 ? 'var(--accent-red)' :
        denial.estimated_denial_probability > 0.2 ? 'var(--accent-amber)' : 'var(--accent-emerald)';

    let html = `<div class="denial-header">
        <div class="dh-stat"><div class="dh-label">Denial Likely</div>
            <div class="dh-value" style="color: ${denial.denial_likely ? 'var(--accent-red)' : 'var(--accent-emerald)'}">
                ${denial.denial_likely ? 'YES' : 'NO'}</div></div>
        <div class="dh-stat"><div class="dh-label">Probability</div>
            <div class="dh-value" style="color: ${probColor}">${(denial.estimated_denial_probability * 100).toFixed(0)}%</div></div>
        <div class="dh-stat"><div class="dh-label">Reasons</div>
            <div class="dh-value">${denial.denial_reasons.length}</div></div>
    </div>`;

    if (denial.denial_reasons.length === 0) {
        html += `<div class="no-denials">✅ No denial triggers identified — low risk of rejection</div>`;
    } else {
        html += denial.denial_reasons.map(r => `
            <div class="denial-reason">
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

    let html = rem.actions.map(a => `
        <div class="remediation-item">
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

    let html = rt.challenges.map(c => `
        <div class="redteam-item">
            <span class="rt-severity severity-${c.severity}">${c.severity}</span>
            <div class="rt-challenge">${c.challenge}</div>
            <div class="rt-recommendation">💡 ${c.recommendation}</div>
        </div>`).join('');

    const riskColor = rt.overall_risk === 'high' ? 'var(--accent-red)' :
        rt.overall_risk === 'medium' ? 'var(--accent-amber)' : 'var(--accent-emerald)';
    html += `<div class="redteam-footer" style="color: ${riskColor}; background: ${riskColor}15; border: 1px solid ${riskColor}30">
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
    container.innerHTML = ''; // clear previous elements
    
    if (activeGraph3D) {
        activeGraph3D._destructor();
        activeGraph3D = null;
    }

    if (!graph || !graph.nodes || graph.nodes.length === 0) return;

    // Mapping colors and types
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
    const height = 500; // Fixed reasonable height for 3D view

    activeGraph3D = ForceGraph3D()(container)
        .width(width)
        .height(height)
        .backgroundColor('#1e293b') // Match background to card
        .graphData(gData)
        .nodeLabel('name')
        .nodeColor(node => nodeColors[node.type] || '#ffffff')
        .nodeResolution(16)
        .linkColor(link => linkColors[link.relation] || '#ffffff')
        .linkWidth(2)
        .linkDirectionalParticles(2)
        .linkDirectionalParticleWidth(2)
        .linkDirectionalParticleSpeed(0.005)
        .onNodeClick(node => {
            // Aim at node from outside it
            const distance = 40;
            const distRatio = 1 + distance/Math.hypot(node.x, node.y, node.z);
            activeGraph3D.cameraPosition(
                { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
                node, // lookAt ({ x, y, z })
                3000  // ms transition duration
            );
        });

    // Render Custom Legend HTML over graph
    const legend = document.createElement('div');
    legend.style.position = 'absolute';
    legend.style.top = '10px';
    legend.style.left = '10px';
    legend.style.color = 'white';
    legend.style.background = 'rgba(0,0,0,0.5)';
    legend.style.padding = '10px';
    legend.style.borderRadius = '8px';
    legend.style.fontFamily = 'Inter, sans-serif';
    legend.style.fontSize = '0.8rem';
    legend.style.pointerEvents = 'none';
    
    legend.innerHTML = `
        <strong>Node Types</strong><br>
        <span style="color:#6366f1">●</span> Fact<br>
        <span style="color:#06b6d4">●</span> Code<br>
        <span style="color:#10b981">●</span> Policy Rule<br>
        <span style="color:#ef4444">●</span> Violation<br>
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
    showToast('Audit JSON copied to clipboard');
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
    showToast('Audit JSON downloaded');
}

// ── Toast ─────────────────────────────────────────────────
function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}
