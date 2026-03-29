"""
EVIDENCE GRAPH BUILDER
──────────────────────
Constructs a graph of facts, codes, policy clauses, and their
relationships (supports / violates / missing).
"""

from __future__ import annotations

from app.schemas import (
    ClinicalExtraction,
    CodeMapping,
    PolicyEvaluation,
    EvidenceGraph,
    GraphNode,
    GraphEdge,
)


def build_evidence_graph(
    extraction: ClinicalExtraction,
    code_mapping: CodeMapping,
    policy_eval: PolicyEvaluation,
) -> EvidenceGraph:
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    node_id = 0

    def _nid():
        nonlocal node_id
        node_id += 1
        return f"N{node_id:03d}"

    # ── Fact nodes ──────────────────────────────────────────
    symptom_ids = []
    for s in extraction.symptoms:
        nid = _nid()
        nodes.append(GraphNode(id=nid, label=f"Symptom: {s}", node_type="fact"))
        symptom_ids.append(nid)

    dur_id = None
    if extraction.duration_weeks is not None:
        dur_id = _nid()
        nodes.append(GraphNode(id=dur_id, label=f"Duration: {extraction.duration_weeks} weeks", node_type="fact"))

    pt_id = None
    if extraction.pt_sessions is not None:
        pt_id = _nid()
        nodes.append(GraphNode(id=pt_id, label=f"PT Sessions: {extraction.pt_sessions}", node_type="fact"))

    med_ids = []
    for m in extraction.medications:
        nid = _nid()
        nodes.append(GraphNode(id=nid, label=f"Medication: {m}", node_type="fact"))
        med_ids.append(nid)

    flag_ids = []
    for f in extraction.red_flags:
        nid = _nid()
        nodes.append(GraphNode(id=nid, label=f"Red Flag: {f}", node_type="fact"))
        flag_ids.append(nid)

    # ── Code nodes ──────────────────────────────────────────
    icd_nid = _nid()
    nodes.append(GraphNode(id=icd_nid, label=f"ICD-10: {code_mapping.icd10_code} ({code_mapping.icd10_description})", node_type="code"))

    cpt_nid = _nid()
    nodes.append(GraphNode(id=cpt_nid, label=f"CPT: {code_mapping.cpt_code} ({code_mapping.cpt_description})", node_type="code"))

    # Symptoms support ICD code
    for sid in symptom_ids:
        edges.append(GraphEdge(source=sid, target=icd_nid, relation="supports"))

    # ── Policy clause nodes ─────────────────────────────────
    for rule in policy_eval.rule_results:
        rnid = _nid()
        ntype = "policy_clause" if rule.passed else "violation"
        nodes.append(GraphNode(id=rnid, label=f"Rule {rule.rule_id}: {rule.description}", node_type=ntype))

        relation = "supports" if rule.passed else "violates"

        # Connect relevant fact node to rule
        if rule.rule_type == "duration" and dur_id:
            edges.append(GraphEdge(source=dur_id, target=rnid, relation=relation))
        elif rule.rule_type == "duration" and not dur_id:
            edges.append(GraphEdge(source=rnid, target=cpt_nid, relation="missing"))
        elif rule.rule_type == "pt_sessions" and pt_id:
            edges.append(GraphEdge(source=pt_id, target=rnid, relation=relation))
        elif rule.rule_type == "pt_sessions" and not pt_id:
            edges.append(GraphEdge(source=rnid, target=cpt_nid, relation="missing"))
        elif rule.rule_type == "medication_trial":
            for mid in med_ids:
                edges.append(GraphEdge(source=mid, target=rnid, relation=relation))
            if not med_ids:
                edges.append(GraphEdge(source=rnid, target=cpt_nid, relation="missing"))
        elif rule.rule_type == "red_flag_override":
            for fid in flag_ids:
                edges.append(GraphEdge(source=fid, target=rnid, relation="supports"))

        # Connect rule to CPT
        edges.append(GraphEdge(source=rnid, target=cpt_nid, relation=relation))

    return EvidenceGraph(nodes=nodes, edges=edges)
