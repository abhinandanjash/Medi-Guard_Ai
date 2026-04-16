"""
DENIAL SIMULATION ENGINE
────────────────────────
Generates realistic denial reasons a payer would use to reject the claim.
Pure rule-based — no LLM.  Mirrors real-world denial language.
"""

from __future__ import annotations

from app.schemas import (
    ClinicalExtraction,
    PolicyEvaluation,
    DenialSimulation,
    DenialReason,
)


def simulate_denials(
    extraction: ClinicalExtraction,
    policy_eval: PolicyEvaluation,
) -> DenialSimulation:
    reasons: list[DenialReason] = []

    for rule in policy_eval.rule_results:
        if rule.passed:
            continue

        if rule.rule_type == "duration":
            reasons.append(DenialReason(
                code="DEN-DUR-001",
                category="Insufficient Duration",
                reason=(
                    f"Clinical documentation does not demonstrate adequate conservative "
                    f"management duration.  Policy requires minimum {rule.required_value} "
                    f"of symptoms; documentation shows {rule.actual_value}."
                ),
                severity="high",
                payer_language=(
                    "The requested service is denied as the clinical information submitted "
                    "does not meet the minimum symptom duration threshold required prior to "
                    "advanced imaging per policy guidelines."
                ),
            ))

        elif rule.rule_type == "pt_sessions":
            reasons.append(DenialReason(
                code="DEN-PT-001",
                category="Incomplete Physical Therapy",
                reason=(
                    f"Insufficient physical therapy documentation.  Policy requires "
                    f"{rule.required_value}; documentation shows {rule.actual_value}."
                ),
                severity="high",
                payer_language=(
                    "Authorization is denied.  The member has not completed the required "
                    "course of physical therapy as outlined in the step-therapy protocol.  "
                    "Please resubmit once the minimum PT requirement has been met."
                ),
            ))

        elif rule.rule_type == "medication_trial":
            reasons.append(DenialReason(
                code="DEN-MED-001",
                category="No Medication Trial Documented",
                reason=(
                    "No documented medication trial found.  Payer requires at least one "
                    "conservative pharmacological intervention before approving imaging."
                ),
                severity="critical",
                payer_language=(
                    "The request is denied due to absence of documented pharmacological "
                    "management.  Step-therapy requirements mandate at least one trial of "
                    "conservative medication (e.g., NSAIDs, muscle relaxants) prior to "
                    "authorization of advanced diagnostic imaging."
                ),
            ))

    # ── Additional denial signals ───────────────────────────
    if not extraction.symptoms:
        reasons.append(DenialReason(
            code="DEN-DOC-001",
            category="Insufficient Clinical Documentation",
            reason="No symptoms documented in the clinical note.",
            severity="critical",
            payer_language=(
                "The submitted documentation does not contain sufficient clinical "
                "information to support medical necessity for the requested service."
            ),
        ))

    if extraction.duration_weeks is not None and extraction.duration_weeks < 2:
        reasons.append(DenialReason(
            code="DEN-ESC-001",
            category="Weak Clinical Escalation",
            reason=(
                "Symptom duration is very short, suggesting premature escalation to "
                "advanced imaging without adequate conservative management."
            ),
            severity="medium",
            payer_language=(
                "Clinical documentation suggests the request for imaging may be "
                "premature.  Additional conservative management is recommended."
            ),
        ))

    # ── Compute denial probability ──────────────────────────
    if policy_eval.red_flag_override:
        prob = 0.05  # red flags make denial very unlikely
    elif not reasons:
        prob = 0.05
    else:
        severity_weights = {"low": 0.1, "medium": 0.2, "high": 0.35, "critical": 0.5}
        prob = min(
            0.95,
            sum(severity_weights.get(r.severity, 0.2) for r in reasons),
        )

    return DenialSimulation(
        denial_likely=prob > 0.3,
        denial_reasons=reasons,
        estimated_denial_probability=round(prob, 2),
    )
