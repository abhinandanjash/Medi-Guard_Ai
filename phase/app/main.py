"""
FastAPI APPLICATION — Prior Authorization Pre-Adjudication Engine
═════════════════════════════════════════════════════════════════
Single POST endpoint runs the full neuro-symbolic pipeline.
Static frontend is served from /static.
"""

from __future__ import annotations

import traceback
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.schemas import AuthorizationRequest, PipelineResponse, UserLogin, UserRegister, AuthResponse, ReportRequest
from app.extractor import extract_clinical_facts
from app.coder import map_codes
from app.policy_engine import evaluate_policy
from app.evidence_graph import build_evidence_graph
from app.denial_engine import simulate_denials
from app.decision_engine import compute_decision
from app.remediation import generate_remediation, assess_completeness
from app.red_team import red_team_review
from app.audit import build_audit_trace

from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import engine, get_db, Base
from app.models import User, Report
import uuid
import json

# Initialize DB
Base.metadata.create_all(bind=engine)

# In-memory simple sessions for prototype
ACTIVE_SESSIONS = {}

# ── App setup ───────────────────────────────────────────────────
app = FastAPI(
    title="Medi-Guard AI",
    version="1.0.0",
    description="Neuro-symbolic pipeline evaluating clinical notes against payer rules",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def serve_frontend():
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "Medi-Guard AI API is running."}

# ── Auth & Session Management ───────────────────────────────────

def get_current_user(x_auth_token: str = Header(None), db: Session = Depends(get_db)):
    if not x_auth_token or x_auth_token not in ACTIVE_SESSIONS:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    user_id = ACTIVE_SESSIONS[x_auth_token]
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@app.post("/api/auth/register", response_model=AuthResponse)
async def register(req: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == req.username).first():
        return AuthResponse(success=False, error="Username already exists")
    
    # Generate unique patient code if registering as patient
    patient_code = None
    if req.role == 'patient':
        import random
        import string
        patient_code = "PT-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
    user = User(
        username=req.username,
        password=req.password,
        role=req.role,
        full_name=req.full_name,
        patient_code=patient_code
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    token = str(uuid.uuid4())
    ACTIVE_SESSIONS[token] = user.id
    return AuthResponse(success=True, token=token, role=user.role, patient_code=patient_code)


@app.post("/api/auth/login", response_model=AuthResponse)
async def login(req: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username, User.password == req.password, User.role == req.role).first()
    if not user:
        return AuthResponse(success=False, error="Invalid credentials")
        
    token = str(uuid.uuid4())
    ACTIVE_SESSIONS[token] = user.id
    return AuthResponse(success=True, token=token, role=user.role, patient_code=user.patient_code)


@app.get("/api/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "role": current_user.role,
        "full_name": current_user.full_name,
        "patient_code": current_user.patient_code
    }


# ── Pipeline endpoint ──────────────────────────────────────────

@app.post("/api/doctor/report", response_model=PipelineResponse)
async def submit_report(req: ReportRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Run the full pre-adjudication pipeline:
    1. Neural extraction
    2. Deterministic code mapping
    3. Symbolic policy evaluation
    4. Evidence graph construction
    5. Denial simulation
    6. Evidence completeness assessment
    7. Decision computation
    8. Remediation plan generation
    9. Red team adversarial review
    10. Audit trace assembly
    """
    try:
        # Ensure only doctors can submit
        if current_user.role != 'doctor':
            return PipelineResponse(success=False, error="Only doctors can submit reports")

        # Get or create patiently based on mobile
        patient = db.query(User).filter(User.username == req.patient_mobile, User.role == 'patient').first()
        if not patient:
            import random, string
            p_code = "PT-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            patient = User(
                username=req.patient_mobile,
                password=req.patient_mobile, # Simple password for prototype
                role='patient',
                full_name=req.patient_name,
                patient_code=p_code
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)

        # Build dummy AuthorizationRequest for internal pipeline functions
        auth_req = AuthorizationRequest(clinical_note=req.clinical_note, payer=req.payer, requested_procedure=req.requested_procedure)

        # STEP 1: Neural extraction
        extraction = extract_clinical_facts(req.clinical_note)
        if req.requested_procedure:
            extraction.requested_procedure = req.requested_procedure

        # STEP 2: Code mapping
        code_mapping = map_codes(extraction)

        # STEP 3: Policy evaluation
        policy_eval = evaluate_policy(req.payer, extraction, code_mapping)

        # STEP 4: Evidence graph
        evidence_graph = build_evidence_graph(extraction, code_mapping, policy_eval)

        # STEP 5: Denial simulation
        denial_sim = simulate_denials(extraction, policy_eval)

        # STEP 6: Evidence completeness
        completeness = assess_completeness(extraction)

        # STEP 7: Decision
        decision = compute_decision(policy_eval, denial_sim, completeness)

        # STEP 8: Remediation
        remediation = generate_remediation(extraction, policy_eval, denial_sim, completeness)

        # STEP 9: Red team review
        red_team = red_team_review(extraction, policy_eval, denial_sim, decision, completeness)

        # STEP 10: Audit trace
        audit = build_audit_trace(
            request=auth_req,
            extraction=extraction,
            code_mapping=code_mapping,
            policy_eval=policy_eval,
            evidence_graph=evidence_graph,
            denial_sim=denial_sim,
            decision=decision,
            remediation=remediation,
            completeness=completeness,
            red_team=red_team,
        )

        # Save to DB
        report = Report(
            patient_id=patient.id,
            doctor_id=current_user.id,
            clinical_note=req.clinical_note,
            requested_procedure=req.requested_procedure,
            payer=req.payer,
            decision_status=decision.status,
            readiness_score=decision.readiness_score,
            audit_json=json.dumps(audit.model_dump())
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        return PipelineResponse(success=True, patient_code=patient.patient_code, audit_trace=audit)

    except Exception as e:
        traceback.print_exc()
        return PipelineResponse(success=False, error=str(e))


@app.get("/api/insurer/reports/search")
async def insurer_search(patient_code: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Search for patient reports by their unique patient code"""
    if current_user.role != 'insurer':
        raise HTTPException(status_code=403, detail="Only insurers can search across patients")
        
    patient = db.query(User).filter(User.patient_code == patient_code).first()
    if not patient:
         raise HTTPException(status_code=404, detail="Patient not found")
         
    reports = db.query(Report).filter(Report.patient_id == patient.id).all()
    results = []
    for r in reports:
        d = r.doctor
        results.append({
            "id": r.id,
            "created_at": r.created_at,
            "doctor_name": d.full_name or d.username if d else "Unknown",
            "clinical_note": r.clinical_note,
            "procedure": r.requested_procedure,
            "decision_status": r.decision_status,
            "readiness_score": r.readiness_score,
            "audit_trace": json.loads(r.audit_json)
        })
    
    return {"patient_name": patient.full_name, "reports": results}


@app.get("/api/patient/reports")
async def patient_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get all reports for the logged in patient"""
    if current_user.role != 'patient':
        raise HTTPException(status_code=403, detail="Only patients can view their own history")
        
    reports = db.query(Report).filter(Report.patient_id == current_user.id).all()
    results = []
    for r in reports:
        d = r.doctor
        results.append({
            "id": r.id,
            "created_at": r.created_at,
            "doctor_name": d.full_name or d.username if d else "Unknown",
            "procedure": r.requested_procedure,
            "payer": r.payer,
            "decision_status": r.decision_status,
            "insurance_approval": "Approved" if r.decision_status == "SUBMISSION_READY" else "Pending Review" if r.decision_status == "NEEDS_REVIEW" else "Blocked",
            "audit_trace": json.loads(r.audit_json)
        })
    
    return {"reports": results}


@app.get("/api/payers")
async def list_payers():
    """Return available payers for the UI dropdown."""
    import json
    policy_path = Path(__file__).parent / "config" / "policies.json"
    with open(policy_path) as f:
        data = json.load(f)
    payers = [p["payer"] for p in data["policies"]]
    return {"payers": payers}


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
