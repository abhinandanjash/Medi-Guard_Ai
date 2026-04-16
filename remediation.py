"""
REMEDIATION ENGINE
──────────────────
Generates actionable remediation steps to improve submission readiness.
"""

from __future__ import annotations

from app.schemas import (
    ClinicalExtraction,
    PolicyEvaluation,
    DenialSimulation,
    RemediationPlan,
    RemediationAction,
    EvidenceCompleteness,
    MissingEvidence,
)


def generate_remediation(
    extraction: ClinicalExtraction,
    policy_eval: PolicyEvaluation,
    denial_sim: DenialSimulation,
    completeness: EvidenceCompleteness,
) -> RemediationPlan:
    actions: list[RemediationAction] = []
    priority = 0

    for rule in policy_eval.rule_results:
        if rule.passed or rule.rule_type == "red_flag_override":
            continue

        priority += 1

        if rule.rule_type == "duration":
            min_weeks = int(rule.required_value.split()[0]) if rule.required_value else 4
            current = extraction.duration_weeks or 0
            gap = max(0, min_weeks - current)
            actions.append(RemediationAction(
                priority=priority,
                category="Conservative Management Duration",
                action=(
                    f"Continue conservative management for at least {gap} more week(s) "
                    f"to meet the {min_weeks}-week minimum requirement.  Document symptom "
                    "persistence at each follow-up visit."
                ),
                impact=f"+{min(15, gap * 3)} readiness points (estimated)",
                estimated_time=f"{gap} weeks",
            ))

        elif rule.rule_type == "pt_sessions":
            min_sessions = int(rule.required_value.split()[0]) if rule.required_value else 6
            current = extraction.pt_sessions or 0
            gap = max(0, min_sessions - current)
            actions.append(RemediationAction(
                priority=priority,
                category="Physical Therapy Completion",
                action=(
                    f"Complete {gap} additional physical therapy session(s) to meet the "
                    f"{min_sessions}-session minimum.  Ensure PT notes document functional "
                    "progress or lack thereof."
                ),
                impact=f"+{min(15, gap * 2)} readiness points (estimated)",
                estimated_time=f"{gap * 1} week(s) at 1 session/week",
            ))

        elif rule.rule_type == "medication_trial":
            actions.append(RemediationAction(
                priority=priority,
                category="Pharmacological Trial",
                action=(
                    "Initiate and document at least one trial of conservative medication "
                    "(e.g., NSAIDs such as ibuprofen or naproxen, or muscle relaxants).  "
                    "Document the medication name, dosage, duration, and patient response."
                ),
                impact="+20 readiness points (estimated)",
                estimated_time="2-4 weeks for adequate trial",
            ))

    # Missing evidence remediations
    for missing in completeness.missing_evidence:
        if missing.importance == "required":
            priority += 1
            actions.append(RemediationAction(
                priority=priority,
                category="Documentation Gap",
                action=f"Document missing required field: {missing.field}",
                impact=f"+{missing.impact_on_score} readiness points (estimated)",
                estimated_time="Immediate (documentation update)",
            ))

    # Estimate post-remediation score
    current_score_loss = sum(
        int(a.impact.split("+")[1].split(" ")[0]) if "+" in a.impact else 0
        for a in actions
    )
    estimated_new = min(100, 85 + min(15, current_score_loss // 3))

    if not actions:
        estimated_new = 95

    return RemediationPlan(
        actions=actions,
        estimated_score_after_remediation=estimated_new,
    )


# ── Negative Evidence / Completeness ──────────────────────────

def assess_completeness(extraction: ClinicalExtraction) -> EvidenceCompleteness:
    """
    Detect missing required and recommended fields.
    This is the NEGATIVE EVIDENCE DETECTOR (bonus feature).
    """
    missing: list[MissingEvidence] = []
    total_fields = 6
    present = 0

    if extraction.symptoms:
        present += 1
    else:
        missing.append(MissingEvidence(
            field="symptoms",
            importance="required",
            impact_on_score=20,
        ))

    if extraction.duration_weeks is not None:
        present += 1
    else:
        missing.append(MissingEvidence(
            field="duration_weeks",
            importance="required",
            impact_on_score=15,
        ))

    if extraction.pt_sessions is not None:
        present += 1
    else:
        missing.append(MissingEvidence(
            field="pt_sessions",
            importance="required",
            impact_on_score=15,
        ))

    if extraction.medications:
        present += 1
    else:
        missing.append(MissingEvidence(
            field="medications",
            importance="required",
            impact_on_score=15,
        ))

    if extraction.treatments_tried:
        present += 1
    else:
        missing.append(MissingEvidence(
            field="treatments_tried",
            importance="recommended",
            impact_on_score=5,
        ))

    if extraction.requested_procedure:
        present += 1
    else:
        missing.append(MissingEvidence(
            field="requested_procedure",
            importance="recommended",
            impact_on_score=5,
        ))

    score = round(present / total_fields, 2)

    return EvidenceCompleteness(
        completeness_score=score,
        missing_evidence=missing,
    )
