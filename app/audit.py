"""
AUDIT TRACE GENERATOR
─────────────────────
Assembles the complete audit trail from all pipeline stages.
Every decision is traceable back to source data.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.schemas import (
    AuthorizationRequest,
    ClinicalExtraction,
    CodeMapping,
    PolicyEvaluation,
    EvidenceGraph,
    DenialSimulation,
    Decision,
    RemediationPlan,
    EvidenceCompleteness,
    RedTeamReport,
    AuditTrace,
)


def build_audit_trace(
    request: AuthorizationRequest,
    extraction: ClinicalExtraction,
    code_mapping: CodeMapping,
    policy_eval: PolicyEvaluation,
    evidence_graph: EvidenceGraph,
    denial_sim: DenialSimulation,
    decision: Decision,
    remediation: RemediationPlan,
    completeness: EvidenceCompleteness,
    red_team: RedTeamReport,
) -> AuditTrace:
    return AuditTrace(
        timestamp=datetime.now(timezone.utc).isoformat(),
        pipeline_version="1.0.0",
        request=request,
        extraction=extraction,
        code_mapping=code_mapping,
        policy_evaluation=policy_eval,
        evidence_graph=evidence_graph,
        denial_simulation=denial_sim,
        decision=decision,
        remediation=remediation,
        evidence_completeness=completeness,
        red_team_report=red_team,
    )
