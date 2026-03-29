"""
TERMINAL DEMO - Prior Auth Pre-Adjudication
Runs the full pipeline with a sample clinical note
"""

import json
import sys
import os
import time

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.schemas import AuthorizationRequest
from app.extractor import extract_clinical_facts
from app.coder import map_codes
from app.policy_engine import evaluate_policy
from app.evidence_graph import build_evidence_graph
from app.denial_engine import simulate_denials
from app.decision_engine import compute_decision
from app.remediation import generate_remediation, assess_completeness
from app.red_team import red_team_review
from app.audit import build_audit_trace


# ── Color helpers ──────────────────────────────────────────────

class C:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def banner(text: str):
    width = 66
    print(f"\n{C.BOLD}{C.CYAN}{'═' * width}")
    print(f"  {text}")
    print(f"{'═' * width}{C.RESET}\n")


def step_header(num: int, title: str):
    print(f"{C.BOLD}{C.BLUE}┌─── STEP {num}: {title}")
    print(f"└{'─' * 60}{C.RESET}")


def success(text: str):
    print(f"  {C.GREEN}✓{C.RESET} {text}")


def fail(text: str):
    print(f"  {C.RED}✗{C.RESET} {text}")


def info(text: str):
    print(f"  {C.DIM}→{C.RESET} {text}")


def warn(text: str):
    print(f"  {C.YELLOW}⚠{C.RESET} {text}")


# ── Sample clinical notes ─────────────────────────────────────

SAMPLE_NOTE_PASS = """
Patient is a 45-year-old male presenting with chronic low back pain for 8 weeks.
Pain radiates to the left leg with numbness and tingling.  Patient has completed
10 sessions of physical therapy with minimal improvement.  Tried ibuprofen 800mg
TID for 4 weeks and cyclobenzaprine 10mg QHS for 3 weeks without significant relief.
Patient reports progressive weakness in left foot (L5 distribution).  Requesting
MRI lumbar spine to evaluate for disc herniation or spinal stenosis.
"""

SAMPLE_NOTE_FAIL = """
Patient complains of back pain for 2 weeks. No prior treatment attempted.
Wants an MRI. No medications tried.
"""

SAMPLE_NOTE_RED_FLAG = """
Patient is a 52-year-old female with acute onset low back pain for 1 week.
Presenting with saddle anesthesia and new-onset bladder dysfunction.
Unable to control urination since yesterday.  Progressive bilateral leg weakness
noted on exam.  Urgent MRI lumbar spine requested to rule out cauda equina syndrome.
"""


def run_pipeline(note: str, payer: str, label: str):
    banner(f"SCENARIO: {label}")
    print(f"{C.DIM}Payer: {payer}{C.RESET}")
    print(f"{C.DIM}Note: {note[:100].strip()}...{C.RESET}\n")

    request = AuthorizationRequest(
        clinical_note=note.strip(),
        payer=payer,
    )

    # ── STEP 1 ─────────────────────────────────────────────
    step_header(1, "CLINICAL FACT EXTRACTION")
    extraction = extract_clinical_facts(request.clinical_note)

    info(f"Symptoms:     {extraction.symptoms}")
    info(f"Duration:     {extraction.duration_weeks} weeks")
    info(f"PT Sessions:  {extraction.pt_sessions}")
    info(f"Medications:  {extraction.medications}")
    info(f"Red Flags:    {extraction.red_flags}")
    info(f"Procedure:    {extraction.requested_procedure}")
    print()

    # ── STEP 2 ─────────────────────────────────────────────
    step_header(2, "CODE MAPPING (Deterministic)")
    codes = map_codes(extraction)

    info(f"ICD-10: {codes.icd10_code} — {codes.icd10_description}")
    info(f"CPT:    {codes.cpt_code} — {codes.cpt_description}")
    info(f"Method: {codes.mapping_method}")
    print()

    # ── STEP 3 ─────────────────────────────────────────────
    step_header(3, "POLICY EVALUATION")
    policy_eval = evaluate_policy(request.payer, extraction)

    info(f"Policy: {policy_eval.policy_id} v{policy_eval.policy_version}")
    info(f"Payer:  {policy_eval.payer}")
    info(f"Red Flag Override: {policy_eval.red_flag_override}")
    print()

    for r in policy_eval.rule_results:
        if r.passed:
            success(f"[{r.rule_id}] {r.rule_type}: {r.detail}")
        else:
            fail(f"[{r.rule_id}] {r.rule_type}: {r.detail}")
    print()

    # ── STEP 4 ─────────────────────────────────────────────
    step_header(4, "EVIDENCE COMPLETENESS")
    completeness = assess_completeness(extraction)

    info(f"Completeness Score: {completeness.completeness_score:.0%}")
    for m in completeness.missing_evidence:
        warn(f"Missing [{m.importance}]: {m.field} (−{m.impact_on_score} pts)")
    if not completeness.missing_evidence:
        success("All evidence fields documented")
    print()

    # ── STEP 5 ─────────────────────────────────────────────
    step_header(5, "DENIAL SIMULATION")
    evidence_graph = build_evidence_graph(extraction, codes, policy_eval)
    denial_sim = simulate_denials(extraction, policy_eval)

    info(f"Denial Likely: {denial_sim.denial_likely}")
    info(f"Estimated Probability: {denial_sim.estimated_denial_probability:.0%}")
    print()

    for dr in denial_sim.denial_reasons:
        fail(f"[{dr.code}] {dr.category}")
        print(f"    {C.DIM}{dr.reason}{C.RESET}")
        print(f"    {C.YELLOW}Payer: \"{dr.payer_language[:120]}...\"{C.RESET}")
        print()

    if not denial_sim.denial_reasons:
        success("No denial triggers identified")
        print()

    # ── STEP 6 ─────────────────────────────────────────────
    step_header(6, "FINAL DECISION")
    decision = compute_decision(policy_eval, denial_sim, completeness)

    status_colors = {
        "SUBMISSION_READY": C.GREEN,
        "NEEDS_MORE_EVIDENCE": C.YELLOW,
        "HIGH_DENIAL_RISK": C.RED,
        "HARD_BLOCK": f"{C.BOLD}{C.RED}",
    }
    color = status_colors.get(decision.status.value, C.RESET)

    print(f"\n  {C.BOLD}STATUS:{C.RESET}  {color}{decision.status.value}{C.RESET}")
    print(f"  {C.BOLD}SCORE:{C.RESET}   {color}{decision.readiness_score}/100{C.RESET}")
    print(f"  {C.BOLD}SUMMARY:{C.RESET} {decision.summary}")
    print()

    # ── STEP 7: Remediation ─────────────────────────────────
    remediation = generate_remediation(extraction, policy_eval, denial_sim, completeness)
    if remediation.actions:
        step_header(7, "REMEDIATION PLAN")
        for a in remediation.actions:
            warn(f"[P{a.priority}] {a.category}")
            print(f"    {C.DIM}{a.action}{C.RESET}")
            print(f"    Impact: {a.impact}  |  Time: {a.estimated_time}")
            print()
        info(f"Estimated score after remediation: {remediation.estimated_score_after_remediation}/100")
        print()

    # ── STEP 8: Red Team ────────────────────────────────────
    red_team = red_team_review(extraction, policy_eval, denial_sim, decision, completeness)
    if red_team.challenges:
        step_header(8, "RED TEAM REVIEW")
        for ch in red_team.challenges:
            warn(f"[{ch.severity.upper()}] {ch.challenge}")
            print(f"    {C.DIM}Recommendation: {ch.recommendation}{C.RESET}")
            print()
        info(f"Overall Red Team Risk: {red_team.overall_risk.upper()}")
        print()

    # ── Build audit ────────────────────────────────────────
    audit = build_audit_trace(
        request=request,
        extraction=extraction,
        code_mapping=codes,
        policy_eval=policy_eval,
        evidence_graph=evidence_graph,
        denial_sim=denial_sim,
        decision=decision,
        remediation=remediation,
        completeness=completeness,
        red_team=red_team,
    )

    return audit


def main():
    banner("PRIOR AUTHORIZATION PRE-ADJUDICATION ENGINE v1.0")
    print(f"{C.DIM}Compliance-Native Neuro-Symbolic Denial-Proofing Compiler{C.RESET}")
    print(f"{C.DIM}────────────────────────────────────────────────────────{C.RESET}\n")

    # Run three scenarios
    audit1 = run_pipeline(SAMPLE_NOTE_PASS, "Generic Insurance", "STRONG CASE — Should Pass")
    print(f"\n{'▓' * 66}\n")

    audit2 = run_pipeline(SAMPLE_NOTE_FAIL, "Blue Cross Blue Shield", "WEAK CASE — Should Fail")
    print(f"\n{'▓' * 66}\n")

    audit3 = run_pipeline(SAMPLE_NOTE_RED_FLAG, "Aetna", "RED FLAG — Emergency Override")

    # ── Save full audit JSON ────────────────────────────────
    banner("AUDIT TRACE OUTPUT")
    output = {
        "scenario_1_strong_case": audit1.model_dump(),
        "scenario_2_weak_case": audit2.model_dump(),
        "scenario_3_red_flag": audit3.model_dump(),
    }

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audit_output.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)

    success(f"Full audit trace saved to: {out_path}")
    print()

    banner("DEMO COMPLETE")


if __name__ == "__main__":
    main()
