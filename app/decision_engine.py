"""
DECISION ENGINE
───────────────
Computes final submission status and readiness score based on
policy evaluation and denial simulation.
"""

from __future__ import annotations

from app.schemas import (
    PolicyEvaluation,
    DenialSimulation,
    EvidenceCompleteness,
    Decision,
    DecisionStatus,
)


def compute_decision(
    policy_eval: PolicyEvaluation,
    denial_sim: DenialSimulation,
    completeness: EvidenceCompleteness,
) -> Decision:
    """
    Deterministic decision logic.  No ML, no LLM.
    """
    # ── Base score calculation ──────────────────────────────
    total_rules = len(policy_eval.rule_results)
    # Exclude red_flag_override from pass/fail count (it's informational)
    scored_rules = [r for r in policy_eval.rule_results if r.rule_type != "red_flag_override"]
    passed_rules = sum(1 for r in scored_rules if r.passed)
    scored_total = max(len(scored_rules), 1)

    rule_score = (passed_rules / scored_total) * 60  # 60% weight

    # Evidence completeness contributes 25%
    completeness_score = completeness.completeness_score * 25

    # Denial probability inversely contributes 15%
    denial_score = (1 - denial_sim.estimated_denial_probability) * 15

    raw_score = rule_score + completeness_score + denial_score

    # Red flag override bonus
    if policy_eval.red_flag_override:
        raw_score = max(raw_score, 85)

    readiness_score = min(100, max(0, int(round(raw_score))))

    # ── Status determination ────────────────────────────────
    failed_rules = [r for r in scored_rules if not r.passed]
    critical_failures = sum(
        1 for r in failed_rules if r.rule_type in ("medication_trial",)
    )

    if policy_eval.red_flag_override:
        status = DecisionStatus.SUBMISSION_READY
        summary = (
            "Red flags detected — step therapy requirements bypassed.  "
            "Submission is recommended with urgency documentation."
        )
    elif readiness_score >= 80 and not failed_rules:
        status = DecisionStatus.SUBMISSION_READY
        summary = (
            "All policy requirements satisfied.  Claim is ready for submission."
        )
    elif readiness_score >= 60 and critical_failures == 0:
        status = DecisionStatus.NEEDS_MORE_EVIDENCE
        summary = (
            f"{len(failed_rules)} rule(s) not fully met.  "
            "Additional documentation or conservative treatment needed."
        )
    elif readiness_score >= 40:
        status = DecisionStatus.HIGH_DENIAL_RISK
        summary = (
            f"High denial risk: {len(failed_rules)} rule(s) failed, "
            f"estimated denial probability {denial_sim.estimated_denial_probability:.0%}.  "
            "Significant remediation required before submission."
        )
    else:
        status = DecisionStatus.HARD_BLOCK
        summary = (
            "Insufficient documentation and unmet requirements.  "
            "Submission at this time would almost certainly be denied."
        )

    return Decision(
        status=status,
        readiness_score=readiness_score,
        summary=summary,
    )
