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

from app.schemas import (AuthorizationRequest, PipelineResponse, UserLogin, UserRegister, AuthResponse,
    ReportRequest, SubmitReportResponse, AdjudicationRequest,
    HospitalSubmissionRequest, HospitalSubmissionResponse,
    PatientHistoryRequest, PatientHistoryResponse,
    SendSummaryRequest, SendSummaryResponse)
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
from app.models import User, Report, PatientMedicalHistory, HospitalSubmission, PatientSummary
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
    return AuthResponse(success=True, token=token, role=user.role, patient_code=patient_code,
                        organization_name=req.organization_name)


@app.post("/api/auth/login", response_model=AuthResponse)
async def login(req: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username, User.password == req.password, User.role == req.role).first()
    if not user:
        return AuthResponse(success=False, error="Invalid credentials")
        
    token = str(uuid.uuid4())
    ACTIVE_SESSIONS[token] = user.id
    return AuthResponse(success=True, token=token, role=user.role, patient_code=user.patient_code,
                        organization_name=user.organization_name)


@app.get("/api/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "role": current_user.role,
        "full_name": current_user.full_name,
        "patient_code": current_user.patient_code,
        "organization_name": current_user.organization_name,
    }


# ── Submit Report (Doctor only — saves to DB, no AI) ──────────

@app.post("/api/doctor/report", response_model=SubmitReportResponse)
async def submit_report(req: ReportRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Submit a clinical report to the database WITHOUT running the AI pipeline."""
    try:
        if current_user.role != 'doctor':
            return SubmitReportResponse(success=False, error="Only doctors can submit reports")

        # Get or create patient based on mobile
        patient = db.query(User).filter(User.username == req.patient_mobile, User.role == 'patient').first()
        if not patient:
            import random, string
            p_code = "PT-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            patient = User(
                username=req.patient_mobile,
                password=req.patient_mobile,
                role='patient',
                full_name=req.patient_name,
                patient_code=p_code
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)

        report = Report(
            patient_id=patient.id,
            doctor_id=current_user.id,
            clinical_note=req.clinical_note,
            requested_procedure=req.requested_procedure,
            payer=req.payer,
            image_data=req.image_data,
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        return SubmitReportResponse(success=True, report_id=report.id, patient_code=patient.patient_code)

    except Exception as e:
        traceback.print_exc()
        return SubmitReportResponse(success=False, error=str(e))


# ── Run Pre-Adjudication (Any role — runs AI on a saved report) ─

@app.post("/api/run-adjudication", response_model=PipelineResponse)
async def run_adjudication(req: AdjudicationRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Run the full neuro-symbolic pre-adjudication pipeline on a saved report.
    Accessible by doctors, insurers, and patients.
    """
    try:
        report = db.query(Report).filter(Report.id == req.report_id).first()
        if not report:
            return PipelineResponse(success=False, error="Report not found")

        # Access control: doctors see their own, patients see theirs, insurers see all
        if current_user.role == 'doctor' and report.doctor_id != current_user.id:
            return PipelineResponse(success=False, error="Access denied")
        if current_user.role == 'patient' and report.patient_id != current_user.id:
            return PipelineResponse(success=False, error="Access denied")

        # Build AuthorizationRequest for the pipeline
        auth_req = AuthorizationRequest(
            clinical_note=report.clinical_note,
            payer=report.payer,
            requested_procedure=report.requested_procedure
        )

        # STEP 1: Neural extraction
        extraction = extract_clinical_facts(report.clinical_note, report.image_data)
        if report.requested_procedure:
            extraction.requested_procedure = report.requested_procedure

        # STEP 2: Code mapping
        code_mapping = map_codes(extraction)

        # STEP 3: Policy evaluation
        policy_eval = evaluate_policy(report.payer, extraction, code_mapping)

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

        # Update the report in DB with AI results
        report.decision_status = decision.status
        report.readiness_score = decision.readiness_score
        report.audit_json = json.dumps(audit.model_dump())
        db.commit()

        patient = db.query(User).filter(User.id == report.patient_id).first()
        return PipelineResponse(success=True, patient_code=patient.patient_code if patient else None, audit_trace=audit)

    except Exception as e:
        traceback.print_exc()
        return PipelineResponse(success=False, error=str(e))


# ── Doctor's own reports ───────────────────────────────────────

@app.get("/api/doctor/reports")
async def doctor_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get all reports submitted by the logged-in doctor"""
    if current_user.role != 'doctor':
        raise HTTPException(status_code=403, detail="Only doctors can view their reports")

    reports = db.query(Report).filter(Report.doctor_id == current_user.id).order_by(Report.id.desc()).all()
    results = []
    for r in reports:
        p = r.patient
        results.append({
            "id": r.id,
            "created_at": r.created_at,
            "patient_name": p.full_name or p.username if p else "Unknown",
            "patient_code": p.patient_code if p else "---",
            "clinical_note": r.clinical_note,
            "procedure": r.requested_procedure,
            "payer": r.payer,
            "image_data": r.image_data,
            "decision_status": r.decision_status,
            "readiness_score": r.readiness_score,
            "has_adjudication": r.audit_json is not None,
        })

    return {"reports": results}


# ── Insurer search ─────────────────────────────────────────────

@app.get("/api/insurer/reports/search")
async def insurer_search(patient_code: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Search for patient reports by their unique patient code"""
    if current_user.role not in ('insurer', 'doctor'):
        raise HTTPException(status_code=403, detail="Only doctors and insurers can search patient records")

    patient = db.query(User).filter(User.patient_code == patient_code).first()
    if not patient:
         raise HTTPException(status_code=404, detail="Patient not found")

    reports = db.query(Report).filter(Report.patient_id == patient.id).order_by(Report.id.desc()).all()
    results = []
    for r in reports:
        d = r.doctor
        results.append({
            "id": r.id,
            "created_at": r.created_at,
            "doctor_name": d.full_name or d.username if d else "Unknown",
            "clinical_note": r.clinical_note,
            "procedure": r.requested_procedure,
            "payer": r.payer,
            "image_data": r.image_data,
            "decision_status": r.decision_status,
            "readiness_score": r.readiness_score,
            "has_adjudication": r.audit_json is not None,
        })

    return {"success": True, "patient_name": patient.full_name, "patient_code": patient.patient_code, "reports": results}


# ── Patient reports ────────────────────────────────────────────

@app.get("/api/patient/reports")
async def patient_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get all reports for the logged in patient"""
    if current_user.role != 'patient':
        raise HTTPException(status_code=403, detail="Only patients can view their own history")

    reports = db.query(Report).filter(Report.patient_id == current_user.id).order_by(Report.id.desc()).all()
    results = []
    for r in reports:
        d = r.doctor
        results.append({
            "id": r.id,
            "created_at": r.created_at,
            "doctor_name": d.full_name or d.username if d else "Unknown",
            "clinical_note": r.clinical_note,
            "procedure": r.requested_procedure,
            "payer": r.payer,
            "image_data": r.image_data,
            "decision_status": r.decision_status,
            "readiness_score": r.readiness_score,
            "has_adjudication": r.audit_json is not None,
        })

    return {"reports": results}


# ── Utilities ──────────────────────────────────────────────────

@app.get("/api/payers")
async def list_payers():
    """Return available payers for the UI dropdown."""
    import json
    policy_path = Path(__file__).parent / "config" / "policies.json"
    with open(policy_path) as f:
        data = json.load(f)
    payers = sorted(set(p["payer"] for p in data["policies"]))
    return {"payers": payers}


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}


# ════════════════════════════════════════════════════════
# PATIENT MEDICAL HISTORY
# ════════════════════════════════════════════════════════

@app.post("/api/patient/medical-history")
async def save_medical_history(req: PatientHistoryRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Patient saves or updates their own medical history."""
    if current_user.role != 'patient':
        raise HTTPException(status_code=403, detail="Only patients can save their medical history")
    try:
        history = db.query(PatientMedicalHistory).filter(PatientMedicalHistory.patient_id == current_user.id).first()
        import datetime as dt
        if history:
            for field, value in req.model_dump().items():
                if value is not None:
                    setattr(history, field, value)
            history.updated_at = dt.datetime.now().isoformat()
        else:
            history = PatientMedicalHistory(patient_id=current_user.id, **req.model_dump())
            db.add(history)
        db.commit()
        return {"success": True, "message": "Medical history saved"}
    except Exception as e:
        traceback.print_exc()
        return {"success": False, "error": str(e)}


@app.get("/api/patient/medical-history")
async def get_my_medical_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Patient views their own medical history."""
    if current_user.role != 'patient':
        raise HTTPException(status_code=403, detail="Only patients can view their own history")
    history = db.query(PatientMedicalHistory).filter(PatientMedicalHistory.patient_id == current_user.id).first()
    if not history:
        return {"success": True, "history": None}
    return {"success": True, "history": {
        "height_cm": history.height_cm, "weight_kg": history.weight_kg, "age": history.age,
        "blood_group": history.blood_group, "past_medical_history": history.past_medical_history,
        "genetic_diseases": history.genetic_diseases, "current_medications": history.current_medications,
        "allergies": history.allergies, "past_surgeries": history.past_surgeries,
        "updated_at": history.updated_at
    }}


# ════════════════════════════════════════════════════════
# HOSPITAL MANAGEMENT ROUTES
# ════════════════════════════════════════════════════════

@app.get("/api/hospital/patient-history/{patient_code}")
async def get_patient_history_for_hospital(patient_code: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Hospital management looks up a patient's medical history by patient code."""
    if current_user.role not in ('hospital', 'doctor'):
        raise HTTPException(status_code=403, detail="Access denied")
    patient = db.query(User).filter(User.patient_code == patient_code).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    history = db.query(PatientMedicalHistory).filter(PatientMedicalHistory.patient_id == patient.id).first()
    return {
        "success": True,
        "patient_name": patient.full_name,
        "patient_code": patient.patient_code,
        "history": {
            "height_cm": history.height_cm if history else None,
            "weight_kg": history.weight_kg if history else None,
            "age": history.age if history else None,
            "blood_group": history.blood_group if history else None,
            "past_medical_history": history.past_medical_history if history else None,
            "genetic_diseases": history.genetic_diseases if history else None,
            "current_medications": history.current_medications if history else None,
            "allergies": history.allergies if history else None,
            "past_surgeries": history.past_surgeries if history else None,
            "updated_at": history.updated_at if history else None,
        } if history else None
    }


@app.post("/api/hospital/submit", response_model=HospitalSubmissionResponse)
async def hospital_submit(req: HospitalSubmissionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Hospital management submits a bill or report for a patient."""
    if current_user.role != 'hospital':
        raise HTTPException(status_code=403, detail="Only hospital accounts can use this endpoint")
    patient = db.query(User).filter(User.patient_code == req.patient_code).first()
    if not patient:
        return HospitalSubmissionResponse(success=False, error="Patient not found with this patient code")
    try:
        sub = HospitalSubmission(
            submitted_by_id=current_user.id, submitter_role='hospital',
            patient_id=patient.id, submission_type=req.submission_type,
            title=req.title, description=req.description,
            amount=req.amount, file_data=req.file_data, patient_admitted=req.patient_admitted
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)
        return HospitalSubmissionResponse(success=True, submission_id=sub.id)
    except Exception as e:
        traceback.print_exc()
        return HospitalSubmissionResponse(success=False, error=str(e))


@app.get("/api/hospital/doctors")
async def list_doctors(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List all registered doctors (for summary target selection)."""
    if current_user.role != 'hospital':
        raise HTTPException(status_code=403, detail="Access denied")
    doctors = db.query(User).filter(User.role == 'doctor').all()
    return {"doctors": [{"id": d.id, "full_name": d.full_name or d.username, "license": d.username} for d in doctors]}


@app.post("/api/hospital/send-summary", response_model=SendSummaryResponse)
async def send_summary_to_doctor(req: SendSummaryRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Hospital sends a medical summary to a selected doctor."""
    if current_user.role != 'hospital':
        raise HTTPException(status_code=403, detail="Access denied")
    patient = db.query(User).filter(User.patient_code == req.patient_code).first()
    if not patient:
        return SendSummaryResponse(success=False, error="Patient not found")
    doctor = db.query(User).filter(User.role == 'doctor', User.id == int(req.doctor_name)).first()
    if not doctor:
        return SendSummaryResponse(success=False, error="Doctor not found")
    try:
        summary = PatientSummary(
            patient_id=patient.id, sent_by_id=current_user.id,
            doctor_id=doctor.id, summary_text=req.summary_text,
            patient_name=patient.full_name or patient.username,
            patient_code=patient.patient_code
        )
        db.add(summary)
        db.commit()
        return SendSummaryResponse(success=True)
    except Exception as e:
        traceback.print_exc()
        return SendSummaryResponse(success=False, error=str(e))


# ════════════════════════════════════════════════════════
# PHARMA ROUTES
# ════════════════════════════════════════════════════════

@app.post("/api/pharma/submit", response_model=HospitalSubmissionResponse)
async def pharma_submit(req: HospitalSubmissionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Pharma submits a bill or report for a patient."""
    if current_user.role != 'pharma':
        raise HTTPException(status_code=403, detail="Only pharma accounts can use this endpoint")
    patient = db.query(User).filter(User.patient_code == req.patient_code).first()
    if not patient:
        return HospitalSubmissionResponse(success=False, error="Patient not found")
    try:
        sub = HospitalSubmission(
            submitted_by_id=current_user.id, submitter_role='pharma',
            patient_id=patient.id, submission_type=req.submission_type,
            title=req.title, description=req.description,
            amount=req.amount, file_data=req.file_data, patient_admitted=req.patient_admitted
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)
        return HospitalSubmissionResponse(success=True, submission_id=sub.id)
    except Exception as e:
        traceback.print_exc()
        return HospitalSubmissionResponse(success=False, error=str(e))


# ════════════════════════════════════════════════════════
# CROSS-ROLE SUBMISSION VISIBILITY
# ════════════════════════════════════════════════════════

def _serialize_submission(s: HospitalSubmission):
    submitter = s.submitted_by
    return {
        "id": s.id, "submission_type": s.submission_type, "title": s.title,
        "description": s.description, "amount": s.amount, "file_data": s.file_data,
        "patient_admitted": s.patient_admitted, "submitter_role": s.submitter_role,
        "submitter_name": submitter.organization_name or submitter.full_name or submitter.username if submitter else "Unknown",
        "created_at": s.created_at
    }


@app.get("/api/patient/submissions")
async def patient_submissions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Patient sees ALL their submissions (bills + reports) from hospital and pharma."""
    if current_user.role != 'patient':
        raise HTTPException(status_code=403, detail="Access denied")
    subs = db.query(HospitalSubmission).filter(HospitalSubmission.patient_id == current_user.id).order_by(HospitalSubmission.id.desc()).all()
    return {"submissions": [_serialize_submission(s) for s in subs]}


@app.get("/api/insurer/submissions/{patient_code}")
async def insurer_submissions(patient_code: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Insurer sees ALL submissions (bills + reports) for a patient."""
    if current_user.role != 'insurer':
        raise HTTPException(status_code=403, detail="Access denied")
    patient = db.query(User).filter(User.patient_code == patient_code).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    subs = db.query(HospitalSubmission).filter(HospitalSubmission.patient_id == patient.id).order_by(HospitalSubmission.id.desc()).all()
    return {"patient_name": patient.full_name, "submissions": [_serialize_submission(s) for s in subs]}


@app.get("/api/doctor/submissions/{patient_code}")
async def doctor_patient_submissions(patient_code: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Doctor sees ONLY reports (not bills) for a patient."""
    if current_user.role != 'doctor':
        raise HTTPException(status_code=403, detail="Access denied")
    patient = db.query(User).filter(User.patient_code == patient_code).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    subs = db.query(HospitalSubmission).filter(
        HospitalSubmission.patient_id == patient.id,
        HospitalSubmission.submission_type != 'bill'
    ).order_by(HospitalSubmission.id.desc()).all()
    return {"patient_name": patient.full_name, "submissions": [_serialize_submission(s) for s in subs]}


@app.get("/api/doctor/summaries")
async def doctor_received_summaries(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Doctor sees medical history summaries sent to them by hospital management."""
    if current_user.role != 'doctor':
        raise HTTPException(status_code=403, detail="Access denied")
    summaries = db.query(PatientSummary).filter(PatientSummary.doctor_id == current_user.id).order_by(PatientSummary.id.desc()).all()
    return {"summaries": [{
        "id": s.id, "patient_name": s.patient_name, "patient_code": s.patient_code,
        "summary_text": s.summary_text,
        "sent_by": s.sent_by.organization_name or s.sent_by.full_name or s.sent_by.username if s.sent_by else "Hospital",
        "created_at": s.created_at
    } for s in summaries]}
