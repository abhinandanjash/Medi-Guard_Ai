"""
Pydantic schemas for structured validation of all data flowing through the engine.
Every layer communicates through these typed models — no raw dicts allowed.
"""

from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import Any, Optional
from enum import Enum

# ── Auth & Database Schemas ────────────────────────────────────

class UserLogin(BaseModel):
    username: str # License, Company, or Mobile
    password: str
    role: str # 'doctor', 'insurer', 'patient'
    
class UserRegister(BaseModel):
    username: str
    password: str
    role: str
    full_name: Optional[str] = None

class AuthResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    role: Optional[str] = None
    patient_code: Optional[str] = None
    error: Optional[str] = None

class ReportRequest(BaseModel):
    patient_mobile: str
    patient_name: str
    clinical_note: str
    payer: str
    requested_procedure: Optional[str] = None

class SubmitReportResponse(BaseModel):
    success: bool
    report_id: Optional[int] = None
    patient_code: Optional[str] = None
    error: Optional[str] = None

class AdjudicationRequest(BaseModel):
    report_id: int

# ── Internal Engine Schemas ────────────────────────────────────


# ═══════════════════════════════════════════════════════════════
# INPUT SCHEMAS
# ═══════════════════════════════════════════════════════════════

class AuthorizationRequest(BaseModel):
    """Incoming request from the API / demo runner."""
    clinical_note: str = Field(..., min_length=20, description="Free-text clinical note")
    payer: str = Field(..., min_length=1, description="Insurance payer name")
    requested_procedure: Optional[str] = Field(None, description="Optional explicit procedure")


# ═══════════════════════════════════════════════════════════════
# EXTRACTION (Neural layer output)
# ═══════════════════════════════════════════════════════════════

class ClinicalExtraction(BaseModel):
    """Structured output expected from the LLM extraction layer."""
    symptoms: list[str] = Field(default_factory=list)
    duration_weeks: Optional[int] = Field(None, ge=0)
    treatments_tried: list[str] = Field(default_factory=list)
    pt_sessions: Optional[int] = Field(None, ge=0)
    medications: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    requested_procedure: Optional[str] = None

    @field_validator("symptoms", "treatments_tried", "medications", "red_flags", mode="before")
    @classmethod
    def ensure_list(cls, v):
        if isinstance(v, str):
            return [v]
        return v or []


# ═══════════════════════════════════════════════════════════════
# CODING
# ═══════════════════════════════════════════════════════════════

class CodeMapping(BaseModel):
    icd10_code: str
    icd10_description: str
    cpt_code: str
    cpt_description: str
    mapping_method: str = "hardcoded_lookup"


# ═══════════════════════════════════════════════════════════════
# POLICY ENGINE
# ═══════════════════════════════════════════════════════════════

class RuleResult(BaseModel):
    rule_id: str
    rule_type: str
    description: str
    passed: bool
    detail: str
    required_value: Optional[str] = None
    actual_value: Optional[str] = None


class PolicyEvaluation(BaseModel):
    payer: str
    policy_id: str
    policy_version: str
    effective_date: str
    all_rules_passed: bool
    red_flag_override: bool
    rule_results: list[RuleResult]


# ═══════════════════════════════════════════════════════════════
# EVIDENCE GRAPH
# ═══════════════════════════════════════════════════════════════

class GraphNode(BaseModel):
    id: str
    label: str
    node_type: str  # fact | code | policy_clause | violation


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str  # supports | violates | missing


class EvidenceGraph(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


# ═══════════════════════════════════════════════════════════════
# DENIAL SIMULATION
# ═══════════════════════════════════════════════════════════════

class DenialReason(BaseModel):
    code: str
    category: str
    reason: str
    severity: str  # low | medium | high | critical
    payer_language: str


class DenialSimulation(BaseModel):
    denial_likely: bool
    denial_reasons: list[DenialReason]
    estimated_denial_probability: float = Field(ge=0.0, le=1.0)


# ═══════════════════════════════════════════════════════════════
# DECISION
# ═══════════════════════════════════════════════════════════════

class DecisionStatus(str, Enum):
    SUBMISSION_READY = "SUBMISSION_READY"
    NEEDS_MORE_EVIDENCE = "NEEDS_MORE_EVIDENCE"
    HIGH_DENIAL_RISK = "HIGH_DENIAL_RISK"
    HARD_BLOCK = "HARD_BLOCK"


class Decision(BaseModel):
    status: DecisionStatus
    readiness_score: int = Field(ge=0, le=100)
    summary: str


# ═══════════════════════════════════════════════════════════════
# REMEDIATION
# ═══════════════════════════════════════════════════════════════

class RemediationAction(BaseModel):
    priority: int
    category: str
    action: str
    impact: str
    estimated_time: Optional[str] = None


class RemediationPlan(BaseModel):
    actions: list[RemediationAction]
    estimated_score_after_remediation: int = Field(ge=0, le=100)


# ═══════════════════════════════════════════════════════════════
# NEGATIVE EVIDENCE / COMPLETENESS
# ═══════════════════════════════════════════════════════════════

class MissingEvidence(BaseModel):
    field: str
    importance: str  # required | recommended
    impact_on_score: int


class EvidenceCompleteness(BaseModel):
    completeness_score: float = Field(ge=0.0, le=1.0)
    missing_evidence: list[MissingEvidence]


# ═══════════════════════════════════════════════════════════════
# RED TEAM
# ═══════════════════════════════════════════════════════════════

class RedTeamChallenge(BaseModel):
    challenge: str
    severity: str
    recommendation: str


class RedTeamReport(BaseModel):
    challenges: list[RedTeamChallenge]
    overall_risk: str  # low | medium | high


# ═══════════════════════════════════════════════════════════════
# AUDIT TRACE (full pipeline output)
# ═══════════════════════════════════════════════════════════════

class AuditTrace(BaseModel):
    timestamp: str
    pipeline_version: str = "1.0.0"
    request: AuthorizationRequest
    extraction: ClinicalExtraction
    code_mapping: CodeMapping
    policy_evaluation: PolicyEvaluation
    evidence_graph: EvidenceGraph
    denial_simulation: DenialSimulation
    decision: Decision
    remediation: RemediationPlan
    evidence_completeness: EvidenceCompleteness
    red_team_report: RedTeamReport


# ═══════════════════════════════════════════════════════════════
# API RESPONSE
# ═══════════════════════════════════════════════════════════════

class PipelineResponse(BaseModel):
    """Top-level API response wrapping the full audit trace."""
    success: bool
    error: Optional[str] = None
    patient_code: Optional[str] = None
    audit_trace: Optional[AuditTrace] = None
