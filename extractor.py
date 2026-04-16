"""
NEURAL EXTRACTION LAYER
───────────────────────
Uses LLM (Groq / Together / OpenAI-compatible) to extract structured clinical
facts from a free-text note.  The LLM is ONLY used for extraction — never for
policy evaluation or decision-making.

Falls back to a regex-based heuristic extractor when no API key is configured,
so the demo always works without external dependencies.
"""

from __future__ import annotations

import json
import os
import re
import base64
import io
from typing import Optional

import requests
from PIL import Image
import google.generativeai as genai

from app.schemas import ClinicalExtraction

# ── Configuration ──────────────────────────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

SYSTEM_PROMPT = """You are a clinical NLP extraction engine.  Given a clinical note,
extract ONLY the following structured data.  Do NOT invent or assume any information
that is not explicitly stated in the note.

Return a single JSON object with these keys:
{
  "symptoms": ["list of symptoms/diagnoses/conditions mentioned"],
  "duration_weeks": <integer or null>,
  "treatments_tried": ["list of treatments/therapies mentioned"],
  "pt_sessions": <integer or null>,
  "medications": ["list of medications mentioned"],
  "red_flags": ["list of red flags mentioned, e.g. cauda equina, progressive weakness"],
  "requested_procedure": "<procedure name or null>"
}

Rules:
- If a value is not found, use null for numbers and [] for lists.
- Do NOT guess ICD/CPT codes.
- Output ONLY valid JSON, no markdown fencing, no commentary."""


def _call_llm(clinical_note: str) -> Optional[dict]:
    """Call Groq API and return parsed JSON, or None on failure."""
    if not GROQ_API_KEY:
        return None

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": clinical_note},
        ],
        "temperature": 0.0,
        "max_tokens": 1024,
    }

    for attempt in range(3):
        try:
            resp = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            # Strip markdown fencing if present
            content = re.sub(r"^```(?:json)?\s*", "", content.strip())
            content = re.sub(r"\s*```$", "", content.strip())
            return json.loads(content)
        except (requests.RequestException, json.JSONDecodeError, KeyError):
            continue
    return None


# ── Heuristic fallback ─────────────────────────────────────────

_DURATION_RE = re.compile(r"(\d+)\s*(?:week|wk)s?", re.IGNORECASE)
_DURATION_MONTH_RE = re.compile(r"(\d+)\s*(?:month|mo)s?", re.IGNORECASE)
_DURATION_YEAR_RE = re.compile(r"(\d+)\s*(?:year|yr)s?", re.IGNORECASE)
_DURATION_DAY_RE = re.compile(r"(\d+)\s*(?:day)s?", re.IGNORECASE)
_PT_RE = re.compile(r"(\d+)\s*(?:session|visit)s?\s*(?:of)?\s*(?:physical therapy|PT)", re.IGNORECASE)
_PT_RE2 = re.compile(r"(?:physical therapy|PT)\s*[:\-–]?\s*(\d+)\s*(?:session|visit)s?", re.IGNORECASE)

_RED_FLAGS = [
    "cauda equina", "saddle anesthesia", "bowel dysfunction",
    "bladder dysfunction", "progressive neurological deficit",
    "progressive weakness", "bilateral leg weakness",
    "unexplained weight loss", "fever with back pain",
    "history of cancer", "iv drug use", "recent trauma", "night pain",
    "loss of consciousness", "sudden onset", "worst headache",
    "chest pain with shortness of breath", "sudden weakness",
    "slurred speech", "vision loss", "blood in stool",
    "blood in urine", "unintentional weight loss",
]

_MEDICATIONS = [
    "ibuprofen", "naproxen", "acetaminophen", "tylenol", "advil",
    "meloxicam", "diclofenac", "cyclobenzaprine", "flexeril",
    "gabapentin", "pregabalin", "prednisone", "methylprednisolone",
    "tramadol", "hydrocodone", "oxycodone", "aspirin", "celecoxib",
    "muscle relaxant", "nsaid", "oral steroids", "epidural injection",
    "corticosteroid", "metformin", "lisinopril", "amlodipine",
    "atorvastatin", "omeprazole", "levothyroxine", "metoprolol",
    "losartan", "albuterol", "fluticasone", "amoxicillin",
    "azithromycin", "ciprofloxacin", "duloxetine", "sertraline",
    "fluoxetine", "sumatriptan", "topiramate", "amitriptyline",
    "baclofen", "tizanidine", "ketorolac", "lidocaine",
]

# Comprehensive symptom / condition detection list
_SYMPTOMS = [
    # Spine
    "low back pain", "lower back pain", "back pain", "lumbar pain", "lumbago",
    "lumbar radiculopathy", "cervical radiculopathy", "radiculopathy",
    "sciatica", "leg pain", "numbness", "tingling",
    "spinal stenosis", "lumbar spinal stenosis", "cervical spinal stenosis",
    "disc herniation", "herniated disc", "lumbar disc herniation", "cervical disc herniation",
    "degenerative disc disease", "spondylosis", "lumbar spondylosis", "cervical spondylosis",
    "spondylolisthesis", "cervical myelopathy",
    "neck pain", "cervical pain", "cervicalgia", "thoracic pain", "mid back pain",
    "whiplash",
    # Shoulder
    "shoulder pain", "rotator cuff tear", "rotator cuff injury", "rotator cuff tendinitis",
    "shoulder impingement", "frozen shoulder", "adhesive capsulitis", "shoulder bursitis",
    # Knee
    "knee pain", "acl tear", "anterior cruciate ligament", "meniscus tear", "torn meniscus",
    "knee osteoarthritis", "knee arthritis", "patellofemoral syndrome",
    "patellar tendinitis", "knee effusion", "knee swelling",
    # Hip
    "hip pain", "hip osteoarthritis", "hip arthritis", "hip bursitis",
    "trochanteric bursitis", "hip fracture", "avascular necrosis",
    # Ankle / Foot
    "ankle sprain", "ankle pain", "plantar fasciitis", "achilles tendinitis", "foot pain",
    # Wrist / Hand / Elbow
    "carpal tunnel syndrome", "carpal tunnel", "tennis elbow", "lateral epicondylitis",
    "golfer's elbow", "medial epicondylitis", "elbow pain", "wrist pain",
    "trigger finger", "de quervain",
    # General MSK
    "osteoarthritis", "arthritis", "rheumatoid arthritis", "gout",
    "fibromyalgia", "myalgia", "muscle pain", "muscle spasm",
    "joint pain", "tendinitis", "bursitis",
    # Neurological
    "headache", "migraine", "tension headache", "neuropathy",
    "peripheral neuropathy", "diabetic neuropathy",
    "seizure", "epilepsy", "multiple sclerosis", "parkinson",
    "stroke", "tia", "dizziness", "vertigo",
    # Cardiac
    "chest pain", "angina", "hypertension", "high blood pressure",
    "heart failure", "atrial fibrillation", "palpitations",
    # Respiratory
    "asthma", "copd", "pneumonia", "bronchitis",
    "shortness of breath", "dyspnea", "cough",
    # GI
    "abdominal pain", "gerd", "acid reflux", "nausea", "vomiting",
    "diarrhea", "constipation",
    # Endocrine
    "diabetes", "type 2 diabetes", "type 1 diabetes",
    "hypothyroidism", "hyperthyroidism", "obesity",
    # Mental health
    "depression", "anxiety", "insomnia",
    # Dermatological
    "rash", "eczema", "psoriasis",
    # General
    "weakness", "fatigue", "swelling", "stiffness",
    "limited range of motion", "radiating pain", "pain",
]

# Procedure detection patterns
_PROCEDURE_PATTERNS = [
    # MRI
    (r"mri\s+(?:of\s+)?(?:the\s+)?lumbar\s*(?:spine)?", "MRI Lumbar Spine"),
    (r"mri\s+(?:of\s+)?(?:the\s+)?cervical\s*(?:spine)?", "MRI Cervical Spine"),
    (r"mri\s+(?:of\s+)?(?:the\s+)?thoracic\s*(?:spine)?", "MRI Thoracic Spine"),
    (r"mri\s+(?:of\s+)?(?:the\s+)?brain", "MRI Brain"),
    (r"mri\s+(?:of\s+)?(?:the\s+)?head", "MRI Brain"),
    (r"mri\s+(?:of\s+)?(?:the\s+)?knee", "MRI Knee"),
    (r"mri\s+(?:of\s+)?(?:the\s+)?shoulder", "MRI Shoulder"),
    (r"mri\s+(?:of\s+)?(?:the\s+)?hip", "MRI Hip"),
    (r"mri\s+(?:of\s+)?(?:the\s+)?ankle", "MRI Ankle"),
    (r"mri\s+(?:of\s+)?(?:the\s+)?wrist", "MRI Wrist"),
    (r"mri\s+(?:of\s+)?(?:the\s+)?elbow", "MRI Elbow"),
    (r"mri\s+(?:of\s+)?(?:the\s+)?abdomen", "MRI Abdomen"),
    (r"mri\s+(?:of\s+)?(?:the\s+)?pelvis", "MRI Pelvis"),
    (r"mri\s+(?:of\s+)?(?:the\s+)?chest", "MRI Chest"),
    (r"mri\s+(?:of\s+)?(?:the\s+)?spine", "MRI Lumbar Spine"),
    (r"\bmri\b", "MRI Lumbar Spine"),
    # CT
    (r"ct\s+(?:scan\s+)?(?:of\s+)?(?:the\s+)?lumbar", "CT Lumbar Spine"),
    (r"ct\s+(?:scan\s+)?(?:of\s+)?(?:the\s+)?cervical", "CT Cervical Spine"),
    (r"ct\s+(?:scan\s+)?(?:of\s+)?(?:the\s+)?head", "CT Head"),
    (r"ct\s+(?:scan\s+)?(?:of\s+)?(?:the\s+)?brain", "CT Brain"),
    (r"ct\s+(?:scan\s+)?(?:of\s+)?(?:the\s+)?abdomen", "CT Abdomen"),
    (r"ct\s+(?:scan\s+)?(?:of\s+)?(?:the\s+)?chest", "CT Chest"),
    (r"\bct\s+scan\b", "CT Scan"),
    # X-Ray
    (r"x-?ray\s+(?:of\s+)?(?:the\s+)?lumbar", "X-Ray Lumbar"),
    (r"x-?ray\s+(?:of\s+)?(?:the\s+)?cervical", "X-Ray Cervical"),
    (r"x-?ray\s+(?:of\s+)?(?:the\s+)?knee", "X-Ray Knee"),
    (r"x-?ray\s+(?:of\s+)?(?:the\s+)?shoulder", "X-Ray Shoulder"),
    (r"x-?ray\s+(?:of\s+)?(?:the\s+)?hip", "X-Ray Hip"),
    (r"x-?ray\s+(?:of\s+)?(?:the\s+)?chest", "X-Ray Chest"),
    (r"\bx-?ray\b", "X-Ray"),
    # Surgeries / Procedures
    (r"total\s+knee\s+replacement", "Total Knee Replacement"),
    (r"knee\s+replacement", "Knee Replacement"),
    (r"total\s+hip\s+replacement", "Total Hip Replacement"),
    (r"hip\s+replacement", "Hip Replacement"),
    (r"knee\s+arthroscopy", "Arthroscopy Knee"),
    (r"shoulder\s+arthroscopy", "Shoulder Arthroscopy"),
    (r"rotator\s+cuff\s+repair", "Rotator Cuff Repair"),
    (r"spinal\s+fusion", "Spinal Fusion"),
    (r"laminectomy", "Laminectomy"),
    (r"discectomy", "Discectomy"),
    (r"epidural\s+injection", "Epidural Injection"),
    (r"nerve\s+block", "Nerve Block"),
    (r"\bemg\b", "EMG"),
    (r"nerve\s+conduction", "Nerve Conduction Study"),
    (r"ultrasound", "Ultrasound"),
]


def _heuristic_extract(note: str) -> dict:
    lower = note.lower()

    # Symptoms — match longer phrases first (more specific)
    sorted_symptoms = sorted(_SYMPTOMS, key=len, reverse=True)
    symptoms = []
    seen = set()
    for s in sorted_symptoms:
        if s in lower and s not in seen:
            # Check it's not a substring of an already-matched longer symptom
            is_substring = any(s in existing and s != existing for existing in seen)
            if not is_substring:
                symptoms.append(s)
                seen.add(s)

    # Duration — try weeks first, then months (convert), then years, then days
    dur_match = _DURATION_RE.search(note)
    if dur_match:
        duration = int(dur_match.group(1))
    else:
        month_match = _DURATION_MONTH_RE.search(note)
        if month_match:
            duration = int(month_match.group(1)) * 4  # approximate weeks
        else:
            year_match = _DURATION_YEAR_RE.search(note)
            if year_match:
                duration = int(year_match.group(1)) * 52
            else:
                day_match = _DURATION_DAY_RE.search(note)
                if day_match:
                    days = int(day_match.group(1))
                    duration = max(1, days // 7)
                else:
                    duration = None

    # PT sessions
    pt_match = _PT_RE.search(note) or _PT_RE2.search(note)
    pt_sessions = int(pt_match.group(1)) if pt_match else None

    # Medications
    meds = []
    seen_meds = set()
    for m in _MEDICATIONS:
        if m in lower and m not in seen_meds:
            meds.append(m)
            seen_meds.add(m)

    # Red flags
    flags = [f for f in _RED_FLAGS if f in lower]

    # Treatments
    treatments = list(meds)
    if pt_sessions is not None or "physical therapy" in lower or " pt " in f" {lower} ":
        treatments.append("physical therapy")

    # Procedure — use regex patterns, first match wins (ordered most specific first)
    procedure = None
    for pattern, proc_name in _PROCEDURE_PATTERNS:
        if re.search(pattern, lower):
            procedure = proc_name
            break

    return {
        "symptoms": symptoms,
        "duration_weeks": duration,
        "treatments_tried": treatments,
        "pt_sessions": pt_sessions,
        "medications": meds,
        "red_flags": flags,
        "requested_procedure": procedure,
    }


# ── Public API ──────────────────────────────────────────────────

def _call_gemini_vlm(clinical_note: str, image_data: Optional[str] = None) -> Optional[dict]:
    """Call Gemini 1.5 Flash VLM and return parsed JSON, or None on failure."""
    if not GOOGLE_API_KEY:
        return None
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        # Content can be a list of text and images
        content = [SYSTEM_PROMPT, f"Clinical Note: {clinical_note}"]
        
        if image_data:
            # Handle potential Data URI prefix
            if "," in image_data:
                image_data = image_data.split(",")[1]
            img_bytes = base64.b64decode(image_data)
            img = Image.open(io.BytesIO(img_bytes))
            content.append(img)
            
        response = model.generate_content(content)
        text = response.text
        # Strip markdown fencing if present
        text = re.sub(r"^```(?:json)?\s*", "", text.strip())
        text = re.sub(r"\s*```$", "", text.strip())
        return json.loads(text)
    except Exception as e:
        print(f"Gemini error: {e}")
        return None


# ── Public API ──────────────────────────────────────────────────

def extract_clinical_facts(clinical_note: str, image_data: Optional[str] = None) -> ClinicalExtraction:
    """
    Extract structured clinical facts from a free-text note and optional image.
    Tries Gemini VLM first (if key exists), then Groq, falls back to heuristic.
    Output is validated through Pydantic.
    """
    raw = None
    method = "none"
    
    # 1. Try Gemini (Multimodal)
    if GOOGLE_API_KEY:
        raw = _call_gemini_vlm(clinical_note, image_data)
        method = "gemini-vlm"
    
    # 2. Try Groq (Text-only)
    if raw is None and GROQ_API_KEY:
        raw = _call_llm(clinical_note)
        method = "groq"

    # 3. Fallback to heuristic
    if raw is None:
        raw = _heuristic_extract(clinical_note)
        method = "heuristic"

    # Validate through Pydantic (retries / coercion handled by schema)
    extraction = ClinicalExtraction(**raw)

    # Log extraction method (useful for audit)
    extraction._extraction_method = method  # type: ignore[attr-defined]
    return extraction
