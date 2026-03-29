"""
RED TEAM AGENT
──────────────
Challenges the decision by looking for weaknesses a payer reviewer
or auditor would exploit.  Pure rule-based adversarial analysis.
"""

from __future__ import annotations

from app.schemas import (
    ClinicalExtraction,
    PolicyEvaluation,
    DenialSimulation,
    Decision,
    EvidenceCompleteness,
    RedTeamReport,
    RedTeamChallenge,
)


def red_team_review(
    extraction: ClinicalExtraction,
    policy_eval: PolicyEvaluation,
    denial_sim: DenialSimulation,
    decision: Decision,
    completeness: EvidenceCompleteness,
) -> RedTeamReport:
    challenges: list[RedTeamChallenge] = []

    # ── Challenge 1: Over-reliance on red flag override ─────
    if policy_eval.red_flag_override:
        failed_before = sum(
            1 for r in policy_eval.rule_results
            if "OVERRIDDEN" in r.detail and r.rule_type != "red_flag_override"
        )
        if failed_before > 0:
            challenges.append(RedTeamChallenge(
                challenge=(
                    f"Decision relies on red flag override to bypass {failed_before} "
                    "failed rule(s).  A medical reviewer may challenge whether the "
                    "documented red flags truly qualify for expedited authorization."
                ),
                severity="medium",
                recommendation=(
                    "Ensure red flag documentation is explicit and supported by "
                    "objective clinical findings (e.g., neurological exam results)."
                ),
            ))

    # ── Challenge 2: Minimal medication documentation ───────
    if len(extraction.medications) == 1:
        challenges.append(RedTeamChallenge(
            challenge=(
                "Only one medication trial documented.  Payer may argue that a single "
                "medication does not constitute an adequate pharmacological trial."
            ),
            severity="low",
            recommendation=(
                "Document at least 2 medication trials from different classes "
                "(e.g., NSAID + muscle relaxant) for stronger justification."
            ),
        ))

    # ── Challenge 3: Low completeness ───────────────────────
    if completeness.completeness_score < 0.7:
        challenges.append(RedTeamChallenge(
            challenge=(
                f"Evidence completeness is only {completeness.completeness_score:.0%}.  "
                "Missing fields create opportunity for payer to request additional "
                "information, delaying authorization."
            ),
            severity="high",
            recommendation=(
                "Fill all required documentation fields before submission.  "
                "Missing evidence is the easiest ground for denial."
            ),
        ))

    # ── Challenge 4: Borderline readiness ───────────────────
    if 50 <= decision.readiness_score <= 75:
        challenges.append(RedTeamChallenge(
            challenge=(
                f"Readiness score of {decision.readiness_score} is borderline.  "
                "Claims in this range have historically higher appeal rates, "
                "suggesting initial denials are common."
            ),
            severity="medium",
            recommendation=(
                "Consider completing all remediation steps before submission "
                "rather than submitting with borderline documentation."
            ),
        ))

    # ── Challenge 5: Short duration with no escalation justification
    if extraction.duration_weeks is not None and extraction.duration_weeks <= 3:
        challenges.append(RedTeamChallenge(
            challenge=(
                f"Only {extraction.duration_weeks} weeks of symptoms documented.  "
                "This is below typical conservative management thresholds.  "
                "A reviewer will question why imaging is being sought this early."
            ),
            severity="high",
            recommendation=(
                "If early imaging is clinically warranted, document specific "
                "escalation triggers (worsening symptoms, functional decline)."
            ),
        ))

    # ── Challenge 6: PT sessions barely meet threshold ──────
    for r in policy_eval.rule_results:
        if r.rule_type == "pt_sessions" and r.passed and extraction.pt_sessions is not None:
            min_val = int(r.required_value.split()[0]) if r.required_value else 6
            if extraction.pt_sessions == min_val:
                challenges.append(RedTeamChallenge(
                    challenge=(
                        f"PT sessions ({extraction.pt_sessions}) exactly meet the minimum "
                        "threshold.  Payer may scrutinize whether therapy was substantive."
                    ),
                    severity="low",
                    recommendation=(
                        "Document PT progress notes showing functional outcomes, "
                        "not just session count."
                    ),
                ))

    # ── Overall risk ────────────────────────────────────────
    if not challenges:
        overall = "low"
    else:
        severities = [c.severity for c in challenges]
        if "high" in severities:
            overall = "high"
        elif "medium" in severities:
            overall = "medium"
        else:
            overall = "low"

    return RedTeamReport(challenges=challenges, overall_risk=overall)
