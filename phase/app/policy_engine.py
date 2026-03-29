"""
SYMBOLIC POLICY ENGINE
──────────────────────
Pure Python rule engine.  Loads payer policies from JSON,
evaluates each rule deterministically against extracted facts.
No LLM, no ML — 100% auditable symbolic logic.

Now matches policies by PAYER + PROCEDURE/CONDITION, not just payer.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.schemas import ClinicalExtraction, CodeMapping, PolicyEvaluation, RuleResult

# ── Load policies ──────────────────────────────────────────────

_POLICY_PATH = Path(__file__).parent / "config" / "policies.json"


def _load_policies() -> list[dict]:
    with open(_POLICY_PATH, "r") as f:
        data = json.load(f)
    return data["policies"]


def _find_policy(payer: str, extraction: ClinicalExtraction, code_mapping: CodeMapping = None) -> dict:
    """
    Find the best-matching policy based on:
      1. Payer name match
      2. CPT code match (if code_mapping provided)
      3. Condition keyword match against symptoms
      4. Fallback to generic payer policy, then to first policy
    """
    policies = _load_policies()
    payer_lower = payer.lower().strip()
    symptoms_lower = [s.lower() for s in extraction.symptoms]
    procedure_lower = (extraction.requested_procedure or "").lower()
    cpt = code_mapping.cpt_code if code_mapping else ""

    # Score each policy
    scored: list[tuple[int, dict]] = []

    for p in policies:
        score = 0
        p_payer = p["payer"].lower()

        # Payer match (required — skip if payer doesn't match)
        if payer_lower not in p_payer and p_payer not in payer_lower:
            # Allow "Generic Insurance" as universal fallback
            if p_payer != "generic insurance":
                continue

        if payer_lower in p_payer or p_payer in payer_lower:
            score += 100  # Strong payer match

        # CPT code match
        if cpt and "cpt_codes" in p:
            if cpt in p["cpt_codes"]:
                score += 50

        # Condition keyword match
        if "condition_keywords" in p:
            keyword_matches = 0
            for kw in p["condition_keywords"]:
                kw_lower = kw.lower()
                # Check symptoms
                for sym in symptoms_lower:
                    if kw_lower in sym or sym in kw_lower:
                        keyword_matches += 1
                        break
                # Check procedure
                if kw_lower in procedure_lower or procedure_lower and kw_lower in procedure_lower:
                    keyword_matches += 1
            score += keyword_matches * 10

        # Procedure name match
        if procedure_lower and "procedure" in p:
            p_proc = p["procedure"].lower()
            if p_proc in procedure_lower or procedure_lower in p_proc:
                score += 40

        if score > 0:
            scored.append((score, p))

    # Sort by score descending, pick the best
    if scored:
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1]

    # Fallback: first policy matching payer, or first Generic policy
    for p in policies:
        if payer_lower in p["payer"].lower():
            return p

    # Ultimate fallback
    return policies[0]


# ── Rule evaluators ────────────────────────────────────────────

def _eval_duration(rule: dict, ext: ClinicalExtraction) -> RuleResult:
    min_weeks = rule["min_weeks"]
    actual = ext.duration_weeks
    passed = actual is not None and actual >= min_weeks

    return RuleResult(
        rule_id=rule["id"],
        rule_type="duration",
        description=rule["description"],
        passed=passed,
        detail=f"Required ≥{min_weeks} weeks, found {actual if actual is not None else 'NOT DOCUMENTED'}",
        required_value=f"{min_weeks} weeks",
        actual_value=f"{actual} weeks" if actual is not None else "Not documented",
    )


def _eval_pt_sessions(rule: dict, ext: ClinicalExtraction) -> RuleResult:
    min_sessions = rule["min_sessions"]
    actual = ext.pt_sessions
    passed = actual is not None and actual >= min_sessions

    return RuleResult(
        rule_id=rule["id"],
        rule_type="pt_sessions",
        description=rule["description"],
        passed=passed,
        detail=f"Required ≥{min_sessions} sessions, found {actual if actual is not None else 'NOT DOCUMENTED'}",
        required_value=f"{min_sessions} sessions",
        actual_value=f"{actual} sessions" if actual is not None else "Not documented",
    )


def _eval_medication_trial(rule: dict, ext: ClinicalExtraction) -> RuleResult:
    has_meds = len(ext.medications) > 0
    passed = has_meds

    return RuleResult(
        rule_id=rule["id"],
        rule_type="medication_trial",
        description=rule["description"],
        passed=passed,
        detail=f"Medications found: {', '.join(ext.medications)}" if has_meds else "No medication trial documented",
        required_value="At least 1 medication trial",
        actual_value=f"{len(ext.medications)} medications" if has_meds else "None",
    )


def _eval_red_flag_override(rule: dict, ext: ClinicalExtraction) -> tuple[RuleResult, bool]:
    """Returns (result, is_override_active)."""
    policy_flags = [f.lower() for f in rule.get("red_flags", [])]
    patient_flags = [f.lower() for f in ext.red_flags]
    matched = [f for f in patient_flags if any(pf in f or f in pf for pf in policy_flags)]
    override = len(matched) > 0

    result = RuleResult(
        rule_id=rule["id"],
        rule_type="red_flag_override",
        description=rule["description"],
        passed=True,
        detail=f"Red flags detected: {', '.join(matched)}.  Step therapy bypassed." if override
        else "No red flags detected.  Standard step therapy applies.",
        required_value="Any qualifying red flag",
        actual_value=", ".join(matched) if matched else "None",
    )
    return result, override


_EVALUATORS = {
    "duration": _eval_duration,
    "pt_sessions": _eval_pt_sessions,
    "medication_trial": _eval_medication_trial,
}


# ── Public API ──────────────────────────────────────────────────

def evaluate_policy(payer: str, extraction: ClinicalExtraction, code_mapping: CodeMapping = None) -> PolicyEvaluation:
    """
    Run every rule in the matched payer+procedure policy against the extraction.
    Returns a full PolicyEvaluation with per-rule pass/fail.
    """
    policy = _find_policy(payer, extraction, code_mapping)
    results: list[RuleResult] = []
    red_flag_override = False

    for rule in policy["rules"]:
        rtype = rule["type"]

        if rtype == "red_flag_override":
            result, red_flag_override = _eval_red_flag_override(rule, extraction)
            results.append(result)
        elif rtype in _EVALUATORS:
            results.append(_EVALUATORS[rtype](rule, extraction))

    # If red flags are present, override failures on step-therapy rules
    if red_flag_override:
        for r in results:
            if r.rule_type in ("duration", "pt_sessions", "medication_trial"):
                r.passed = True
                r.detail += "  [OVERRIDDEN BY RED FLAG]"

    all_passed = all(r.passed for r in results)

    return PolicyEvaluation(
        payer=policy["payer"],
        policy_id=policy["policy_id"],
        policy_version=policy["version"],
        effective_date=policy["effective_date"],
        all_rules_passed=all_passed,
        red_flag_override=red_flag_override,
        rule_results=results,
    )
