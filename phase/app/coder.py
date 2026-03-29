"""
CODING LAYER
────────────
Deterministic ICD-10 / CPT mapping.
NO LLM involvement — hardcoded lookups only for the MVP.
This guarantees zero hallucinated codes.

Expanded to cover orthopedic, neurological, musculoskeletal,
and common primary care conditions.
"""

from __future__ import annotations

from app.schemas import ClinicalExtraction, CodeMapping

# ── Hardcoded ICD-10 mapping table ────────────────────────────
# Ordered from MOST SPECIFIC to LEAST SPECIFIC within each body region.
# The matcher picks the best (most specific) match.

_ICD10_MAP: dict[str, tuple[str, str]] = {
    # ── Lumbar / Low back ─────────────────────────────────────
    "lumbar radiculopathy":          ("M54.16",  "Radiculopathy, lumbar region"),
    "lumbar disc herniation":        ("M51.16",  "Intervertebral disc disorders with radiculopathy, lumbar region"),
    "disc herniation":               ("M51.16",  "Intervertebral disc disorders with radiculopathy, lumbar region"),
    "herniated disc":                ("M51.16",  "Intervertebral disc disorders with radiculopathy, lumbar region"),
    "lumbar spinal stenosis":        ("M48.06",  "Spinal stenosis, lumbar region"),
    "spinal stenosis":               ("M48.06",  "Spinal stenosis, lumbar region"),
    "lumbar spondylosis":            ("M47.816", "Spondylosis without myelopathy, lumbar region"),
    "spondylosis":                   ("M47.819", "Spondylosis without myelopathy, site unspecified"),
    "spondylolisthesis":             ("M43.10",  "Spondylolisthesis, site unspecified"),
    "degenerative disc disease":     ("M51.36",  "Other intervertebral disc degeneration, lumbar region"),
    "low back pain":                 ("M54.50",  "Low back pain, unspecified"),
    "lower back pain":               ("M54.50",  "Low back pain, unspecified"),
    "back pain":                     ("M54.5",   "Low back pain"),
    "lumbar pain":                   ("M54.50",  "Low back pain, unspecified"),
    "lumbago":                       ("M54.50",  "Low back pain, unspecified"),
    "sciatica":                      ("M54.30",  "Sciatica, unspecified side"),
    "radiculopathy":                 ("M54.10",  "Radiculopathy, site unspecified"),

    # ── Cervical / Neck ───────────────────────────────────────
    "cervical radiculopathy":        ("M54.12",  "Radiculopathy, cervical region"),
    "cervical disc herniation":      ("M50.20",  "Other cervical disc displacement, unspecified cervical region"),
    "cervical spinal stenosis":      ("M48.02",  "Spinal stenosis, cervical region"),
    "cervical spondylosis":          ("M47.812", "Spondylosis without myelopathy, cervical region"),
    "cervical myelopathy":           ("M47.12",  "Other spondylosis with myelopathy, cervical region"),
    "cervical pain":                 ("M54.2",   "Cervicalgia"),
    "cervicalgia":                   ("M54.2",   "Cervicalgia"),
    "neck pain":                     ("M54.2",   "Cervicalgia"),
    "whiplash":                      ("S13.4",   "Sprain of ligaments of cervical spine"),

    # ── Thoracic ──────────────────────────────────────────────
    "thoracic pain":                 ("M54.6",   "Pain in thoracic spine"),
    "thoracic back pain":            ("M54.6",   "Pain in thoracic spine"),
    "mid back pain":                 ("M54.6",   "Pain in thoracic spine"),

    # ── Shoulder ──────────────────────────────────────────────
    "rotator cuff tear":             ("M75.10",  "Rotator cuff tear, unspecified shoulder"),
    "rotator cuff injury":           ("M75.10",  "Rotator cuff tear, unspecified shoulder"),
    "rotator cuff tendinitis":       ("M75.10",  "Rotator cuff tear, unspecified shoulder"),
    "shoulder impingement":          ("M75.40",  "Impingement syndrome of unspecified shoulder"),
    "frozen shoulder":               ("M75.00",  "Adhesive capsulitis of unspecified shoulder"),
    "adhesive capsulitis":           ("M75.00",  "Adhesive capsulitis of unspecified shoulder"),
    "shoulder pain":                 ("M25.519", "Pain in unspecified shoulder"),
    "shoulder bursitis":             ("M75.50",  "Bursitis of unspecified shoulder"),

    # ── Knee ──────────────────────────────────────────────────
    "acl tear":                      ("S83.519", "Sprain of anterior cruciate ligament of unspecified knee"),
    "anterior cruciate ligament":    ("S83.519", "Sprain of anterior cruciate ligament of unspecified knee"),
    "meniscus tear":                 ("S83.209", "Unspecified tear of unspecified meniscus, unspecified knee"),
    "torn meniscus":                 ("S83.209", "Unspecified tear of unspecified meniscus, unspecified knee"),
    "knee osteoarthritis":           ("M17.9",   "Osteoarthritis of knee, unspecified"),
    "knee arthritis":                ("M17.9",   "Osteoarthritis of knee, unspecified"),
    "knee pain":                     ("M25.569", "Pain in unspecified knee"),
    "patellofemoral syndrome":       ("M22.2X9", "Patellofemoral disorders, unspecified knee"),
    "patellar tendinitis":           ("M76.50",  "Patellar tendinitis, unspecified knee"),
    "knee effusion":                 ("M25.469", "Effusion, unspecified knee"),
    "knee swelling":                 ("M25.469", "Effusion, unspecified knee"),

    # ── Hip ───────────────────────────────────────────────────
    "hip osteoarthritis":            ("M16.9",   "Osteoarthritis of hip, unspecified"),
    "hip arthritis":                 ("M16.9",   "Osteoarthritis of hip, unspecified"),
    "hip pain":                      ("M25.559", "Pain in unspecified hip"),
    "hip bursitis":                  ("M70.60",  "Trochanteric bursitis, unspecified hip"),
    "trochanteric bursitis":         ("M70.60",  "Trochanteric bursitis, unspecified hip"),
    "hip fracture":                  ("S72.009", "Fracture of unspecified part of neck of unspecified femur"),
    "avascular necrosis hip":        ("M87.059", "Idiopathic aseptic necrosis of unspecified femur"),

    # ── Ankle / Foot ──────────────────────────────────────────
    "ankle sprain":                  ("S93.409", "Sprain of unspecified ligament of unspecified ankle"),
    "ankle pain":                    ("M25.579", "Pain in unspecified ankle and joints of unspecified foot"),
    "plantar fasciitis":             ("M72.2",   "Plantar fascial fibromatosis"),
    "achilles tendinitis":           ("M76.60",  "Achilles tendinitis, unspecified leg"),
    "foot pain":                     ("M79.671", "Pain in right foot"),

    # ── Wrist / Hand / Elbow ──────────────────────────────────
    "carpal tunnel syndrome":        ("G56.00",  "Carpal tunnel syndrome, unspecified upper limb"),
    "carpal tunnel":                 ("G56.00",  "Carpal tunnel syndrome, unspecified upper limb"),
    "tennis elbow":                  ("M77.10",  "Lateral epicondylitis, unspecified elbow"),
    "lateral epicondylitis":         ("M77.10",  "Lateral epicondylitis, unspecified elbow"),
    "golfer's elbow":                ("M77.00",  "Medial epicondylitis, unspecified elbow"),
    "medial epicondylitis":          ("M77.00",  "Medial epicondylitis, unspecified elbow"),
    "elbow pain":                    ("M25.529", "Pain in unspecified elbow"),
    "wrist pain":                    ("M25.539", "Pain in unspecified wrist"),
    "trigger finger":                ("M65.30",  "Trigger finger, unspecified finger"),
    "de quervain":                   ("M65.4",   "Radial styloid tenosynovitis [de Quervain]"),

    # ── General musculoskeletal ───────────────────────────────
    "osteoarthritis":                ("M19.90",  "Unspecified osteoarthritis, unspecified site"),
    "arthritis":                     ("M19.90",  "Unspecified osteoarthritis, unspecified site"),
    "rheumatoid arthritis":          ("M06.9",   "Rheumatoid arthritis, unspecified"),
    "gout":                          ("M10.9",   "Gout, unspecified"),
    "fibromyalgia":                  ("M79.7",   "Fibromyalgia"),
    "myalgia":                       ("M79.1",   "Myalgia"),
    "muscle pain":                   ("M79.1",   "Myalgia"),
    "muscle spasm":                  ("M62.830", "Muscle spasm of back"),
    "joint pain":                    ("M25.50",  "Pain in unspecified joint"),
    "tendinitis":                    ("M77.9",   "Enthesopathy, unspecified"),
    "bursitis":                      ("M71.9",   "Bursopathy, unspecified"),

    # ── Neurological ──────────────────────────────────────────
    "headache":                      ("R51.9",   "Headache, unspecified"),
    "migraine":                      ("G43.909", "Migraine, unspecified, not intractable, without status migrainosus"),
    "tension headache":              ("G44.209", "Tension-type headache, unspecified, not intractable"),
    "neuropathy":                    ("G62.9",   "Polyneuropathy, unspecified"),
    "peripheral neuropathy":         ("G62.9",   "Polyneuropathy, unspecified"),
    "diabetic neuropathy":           ("E11.40",  "Type 2 diabetes with diabetic neuropathy, unspecified"),
    "seizure":                       ("R56.9",   "Unspecified convulsions"),
    "epilepsy":                      ("G40.909", "Epilepsy, unspecified, not intractable, without status epilepticus"),
    "multiple sclerosis":            ("G35",     "Multiple sclerosis"),
    "parkinson":                     ("G20",     "Parkinson's disease"),
    "stroke":                        ("I63.9",   "Cerebral infarction, unspecified"),
    "tia":                           ("G45.9",   "Transient cerebral ischemic attack, unspecified"),

    # ── Chest / Cardiac ───────────────────────────────────────
    "chest pain":                    ("R07.9",   "Chest pain, unspecified"),
    "angina":                        ("I20.9",   "Angina pectoris, unspecified"),
    "hypertension":                  ("I10",     "Essential (primary) hypertension"),
    "high blood pressure":           ("I10",     "Essential (primary) hypertension"),
    "heart failure":                 ("I50.9",   "Heart failure, unspecified"),
    "atrial fibrillation":           ("I48.91",  "Unspecified atrial fibrillation"),
    "palpitations":                  ("R00.2",   "Palpitations"),

    # ── Respiratory ───────────────────────────────────────────
    "asthma":                        ("J45.909", "Unspecified asthma, uncomplicated"),
    "copd":                          ("J44.1",   "Chronic obstructive pulmonary disease with acute exacerbation"),
    "pneumonia":                     ("J18.9",   "Pneumonia, unspecified organism"),
    "bronchitis":                    ("J20.9",   "Acute bronchitis, unspecified"),
    "shortness of breath":          ("R06.00",  "Dyspnea, unspecified"),
    "dyspnea":                       ("R06.00",  "Dyspnea, unspecified"),
    "cough":                         ("R05.9",   "Cough, unspecified"),

    # ── GI ────────────────────────────────────────────────────
    "abdominal pain":                ("R10.9",   "Unspecified abdominal pain"),
    "gerd":                          ("K21.0",   "Gastro-esophageal reflux disease with esophagitis"),
    "acid reflux":                   ("K21.0",   "Gastro-esophageal reflux disease with esophagitis"),
    "nausea":                        ("R11.0",   "Nausea"),
    "vomiting":                      ("R11.10",  "Vomiting, unspecified"),
    "diarrhea":                      ("R19.7",   "Diarrhea, unspecified"),
    "constipation":                  ("K59.00",  "Constipation, unspecified"),

    # ── Endocrine ─────────────────────────────────────────────
    "diabetes":                      ("E11.9",   "Type 2 diabetes mellitus without complications"),
    "type 2 diabetes":               ("E11.9",   "Type 2 diabetes mellitus without complications"),
    "type 1 diabetes":               ("E10.9",   "Type 1 diabetes mellitus without complications"),
    "hypothyroidism":                ("E03.9",   "Hypothyroidism, unspecified"),
    "hyperthyroidism":               ("E05.90",  "Thyrotoxicosis, unspecified"),
    "obesity":                       ("E66.9",   "Obesity, unspecified"),

    # ── Mental health ─────────────────────────────────────────
    "depression":                    ("F32.9",   "Major depressive disorder, single episode, unspecified"),
    "anxiety":                       ("F41.9",   "Anxiety disorder, unspecified"),
    "insomnia":                      ("G47.00",  "Insomnia, unspecified"),

    # ── Dermatological ────────────────────────────────────────
    "rash":                          ("R21",     "Rash and other nonspecific skin eruption"),
    "eczema":                        ("L30.9",   "Dermatitis, unspecified"),
    "psoriasis":                     ("L40.9",   "Psoriasis, unspecified"),

    # ── Catch-all ─────────────────────────────────────────────
    "pain":                          ("R52",     "Pain, unspecified"),
    "numbness":                      ("R20.0",   "Anesthesia of skin"),
    "tingling":                      ("R20.2",   "Paresthesia of skin"),
    "weakness":                      ("R53.1",   "Weakness"),
    "fatigue":                       ("R53.83",  "Other fatigue"),
    "swelling":                      ("R60.0",   "Localized edema"),
    "stiffness":                     ("M25.60",  "Stiffness of unspecified joint, not elsewhere classified"),
    "limited range of motion":       ("M25.60",  "Stiffness of unspecified joint, not elsewhere classified"),
    "radiating pain":                ("M54.10",  "Radiculopathy, site unspecified"),
    "leg pain":                      ("M79.669", "Pain in unspecified lower leg"),
}

# ── CPT procedure mapping ─────────────────────────────────────

_CPT_MAP: dict[str, tuple[str, str]] = {
    # Spine MRI
    "mri lumbar spine":              ("72148", "MRI lumbar spine without contrast"),
    "mri lumbar":                    ("72148", "MRI lumbar spine without contrast"),
    "mri cervical spine":            ("72141", "MRI cervical spine without contrast"),
    "mri cervical":                  ("72141", "MRI cervical spine without contrast"),
    "mri thoracic spine":            ("72146", "MRI thoracic spine without contrast"),
    "mri thoracic":                  ("72146", "MRI thoracic spine without contrast"),
    "mri spine":                     ("72148", "MRI lumbar spine without contrast"),

    # Other MRI
    "mri brain":                     ("70553", "MRI brain without contrast, then with contrast"),
    "mri head":                      ("70553", "MRI brain without contrast, then with contrast"),
    "mri knee":                      ("73721", "MRI any joint of lower extremity without contrast"),
    "mri shoulder":                  ("73221", "MRI any joint of upper extremity without contrast"),
    "mri hip":                       ("73721", "MRI any joint of lower extremity without contrast"),
    "mri ankle":                     ("73721", "MRI any joint of lower extremity without contrast"),
    "mri wrist":                     ("73221", "MRI any joint of upper extremity without contrast"),
    "mri elbow":                     ("73221", "MRI any joint of upper extremity without contrast"),
    "mri abdomen":                   ("74181", "MRI abdomen without contrast"),
    "mri pelvis":                    ("72195", "MRI pelvis without contrast"),
    "mri chest":                     ("71550", "MRI chest without contrast"),

    # CT
    "ct lumbar spine":               ("72131", "CT lumbar spine without contrast"),
    "ct cervical spine":             ("72125", "CT cervical spine without contrast"),
    "ct head":                       ("70450", "CT head/brain without contrast"),
    "ct brain":                      ("70450", "CT head/brain without contrast"),
    "ct abdomen":                    ("74150", "CT abdomen without contrast"),
    "ct chest":                      ("71250", "CT chest without contrast"),
    "ct scan":                       ("74150", "CT abdomen without contrast"),

    # X-Ray
    "x-ray lumbar":                  ("72100", "Radiologic exam, lumbosacral spine, 2-3 views"),
    "x-ray cervical":                ("72040", "Radiologic exam, cervical spine, 2-3 views"),
    "x-ray knee":                    ("73562", "Radiologic exam, knee, 3 views"),
    "x-ray shoulder":                ("73030", "Radiologic exam, shoulder, 2 views"),
    "x-ray hip":                     ("73502", "Radiologic exam, hip, 2-3 views"),
    "x-ray chest":                   ("71046", "Radiologic exam, chest, 2 views"),
    "x-ray":                         ("72100", "Radiologic exam, lumbosacral spine, 2-3 views"),

    # Surgeries / procedures
    "total knee replacement":        ("27447", "Total knee arthroplasty"),
    "knee replacement":              ("27447", "Total knee arthroplasty"),
    "total hip replacement":         ("27130", "Total hip arthroplasty"),
    "hip replacement":               ("27130", "Total hip arthroplasty"),
    "arthroscopy knee":              ("29881", "Arthroscopy, knee, surgical; with meniscectomy"),
    "knee arthroscopy":              ("29881", "Arthroscopy, knee, surgical; with meniscectomy"),
    "rotator cuff repair":           ("23412", "Repair of ruptured musculotendinous cuff"),
    "shoulder arthroscopy":          ("29826", "Arthroscopy, shoulder, surgical; decompression"),
    "spinal fusion":                 ("22612", "Arthrodesis, posterior or posterolateral technique, lumbar"),
    "laminectomy":                   ("63047", "Laminectomy for decompression, lumbar"),
    "discectomy":                    ("63030", "Laminotomy with disc excision, lumbar"),
    "epidural injection":            ("62323", "Injection, epidural, lumbar or sacral"),
    "nerve block":                   ("64483", "Injection, transforaminal epidural, lumbar"),
    "emg":                           ("95907", "Nerve conduction studies, 1-2 studies"),
    "nerve conduction study":        ("95907", "Nerve conduction studies, 1-2 studies"),
    "ultrasound":                    ("76881", "Ultrasound, joint, real-time with image documentation"),
    "physical therapy":              ("97110", "Therapeutic exercises"),
    "pt evaluation":                 ("97161", "Physical therapy evaluation, low complexity"),
}

# ── LLM-assisted code mapping (fallback) ──────────────────────

import json
import os
import re
import requests

_GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
_GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

_CODE_MAPPING_PROMPT = """You are a medical coding assistant. Given a list of symptoms/conditions,
return the SINGLE most appropriate ICD-10-CM code and CPT code.

You MUST return ONLY a valid JSON object in this exact format:
{
  "icd10_code": "<code>",
  "icd10_description": "<description>",
  "cpt_code": "<code>",
  "cpt_description": "<description>"
}

Rules:
- Use the most specific ICD-10-CM code that matches the primary condition.
- For CPT, use the most relevant procedure code if a procedure is mentioned, otherwise use 99213.
- Do NOT invent codes. Use only real, valid ICD-10-CM and CPT codes.
- Output ONLY the JSON object, no markdown, no commentary."""


def _llm_map_codes(symptoms: list[str], procedure: str | None) -> tuple[str, str, str, str] | None:
    """Call LLM to map symptoms to ICD-10/CPT codes. Returns (icd_code, icd_desc, cpt_code, cpt_desc) or None."""
    if not _GROQ_API_KEY:
        return None

    prompt = f"Symptoms/Conditions: {', '.join(symptoms)}"
    if procedure:
        prompt += f"\nRequested Procedure: {procedure}"

    headers = {
        "Authorization": f"Bearer {_GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": _GROQ_MODEL,
        "messages": [
            {"role": "system", "content": _CODE_MAPPING_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 256,
    }

    try:
        resp = requests.post(_GROQ_URL, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        content = re.sub(r"^```(?:json)?\s*", "", content.strip())
        content = re.sub(r"\s*```$", "", content.strip())
        data = json.loads(content)
        return (
            data.get("icd10_code", "R69"),
            data.get("icd10_description", "Illness, unspecified"),
            data.get("cpt_code", "99213"),
            data.get("cpt_description", "Office visit"),
        )
    except Exception:
        return None


def map_codes(extraction: ClinicalExtraction) -> CodeMapping:
    """
    Map extracted clinical facts to ICD-10 and CPT codes.

    Strategy (3-tier):
      1. Hardcoded lookup table (fastest, most reliable)
      2. Substring fuzzy matching against the table
      3. LLM-assisted mapping (fallback for unknown conditions)
    """
    # ── ICD-10: pick the most specific symptom match ──
    icd_code, icd_desc = None, None
    mapping_method = "hardcoded_lookup"

    # Tier 1: Direct match — prefer longer (more specific) matches
    best_match_len = 0
    for symptom in extraction.symptoms:
        key = symptom.lower().strip()
        if key in _ICD10_MAP and len(key) > best_match_len:
            icd_code, icd_desc = _ICD10_MAP[key]
            best_match_len = len(key)

    # Tier 2: Substring fuzzy match
    if icd_code is None:
        for symptom in extraction.symptoms:
            key = symptom.lower().strip()
            for map_key, (code, desc) in _ICD10_MAP.items():
                if map_key in key or key in map_key:
                    if len(map_key) > best_match_len:
                        icd_code, icd_desc = code, desc
                        best_match_len = len(map_key)

    # ── CPT: match requested procedure ──
    cpt_code, cpt_desc = None, None
    proc = (extraction.requested_procedure or "").lower().strip()

    if proc:
        cpt_best_len = 0
        if proc in _CPT_MAP:
            cpt_code, cpt_desc = _CPT_MAP[proc]
        else:
            for proc_key, (code, desc) in _CPT_MAP.items():
                if proc_key in proc or proc in proc_key:
                    if len(proc_key) > cpt_best_len:
                        cpt_code, cpt_desc = code, desc
                        cpt_best_len = len(proc_key)

    # Tier 3: LLM fallback if either code is still missing
    if icd_code is None or cpt_code is None:
        llm_result = _llm_map_codes(extraction.symptoms, extraction.requested_procedure)
        if llm_result:
            llm_icd, llm_icd_desc, llm_cpt, llm_cpt_desc = llm_result
            if icd_code is None:
                icd_code, icd_desc = llm_icd, llm_icd_desc
                mapping_method = "llm_assisted"
            if cpt_code is None:
                cpt_code, cpt_desc = llm_cpt, llm_cpt_desc
                mapping_method = "llm_assisted"

    # Final fallback
    if icd_code is None:
        icd_code, icd_desc = "R69", "Illness, unspecified"
    if cpt_code is None:
        cpt_code, cpt_desc = "99213", "Office/outpatient visit, established patient, low complexity"

    return CodeMapping(
        icd10_code=icd_code,
        icd10_description=icd_desc,
        cpt_code=cpt_code,
        cpt_description=cpt_desc,
        mapping_method=mapping_method,
    )

