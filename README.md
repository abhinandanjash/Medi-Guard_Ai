<div align="center">
  
# 🛡️ Medi-Guard AI

**The Neuro-Symbolic Prior Authorization & Pre-Adjudication Engine**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/release/python-390/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.103.2-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Groq API](https://img.shields.io/badge/Groq%20Llama%203-Powered-f3f4f6?logo=groq)](https://groq.com)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=flat&logo=sqlite&logoColor=white)](https://sqlite.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

*Eliminate healthcare claim denials before they happen.*

---

[Key Features](#-key-features) • [Architecture](#%EF%B8%8F-neuro-symbolic-architecture) • [Portals](#-multi-role-web-portals) • [Installation](#-getting-started) • [Usage](#-how-to-use) • [Screenshots](#-screenshots)

</div>

## 📖 Overview

**Medi-Guard AI** is an advanced, neuro-symbolic engine designed to automatically evaluate raw clinical notes against strict insurance payer rules *before* claims are submitted.

By combining the natural language understanding of Large Language Models (LLMs) with the absolute, deterministic reasoning of a symbolic Python rule engine, Medi-Guard AI **eliminates AI hallucinations** in the final decision-making process. The result is a fully auditable pipeline that tells doctors exactly *why* a claim might be denied and exactly *how* to fix it.

---

## 🌟 Key Features

*   **🛡️ Hallucination-Free Adjudication**: Neural networks extract facts (symptoms, durations), while a hard-coded symbolic logic engine enforces the insurance policies.
*   **📊 3D Evidence Graph Visualization**: An interactive, physics-based 3D graph visualizes exactly which clinical facts support or violate which policy clauses.
*   **🔧 Auto-Remediation Plans**: Automatically generates actionable next steps (e.g., "Complete 2 more weeks of Physical Therapy") if a claim evaluates poorly.
*   **🏥 Multi-Role Authentication**: Distinct dashboards and workflows for **Doctors**, **Insurers**, and **Patients**.
*   **💼 Secure Claim Linking**: Automatically generates unique, secure `Patient Codes` (e.g., `PT-A1B2C3`) that tie claims directly to anonymous searching for insurers.

---

## ⚙️ Neuro-Symbolic Architecture

Medi-Guard uses a **Pipeline-Driven** architecture consisting of distinct layers:

1.  **Neural Extraction Layer**: Uses Groq (`llama-3.3-70b-versatile`) to extract symptoms, duration parameters, medications, and treatments tried from noisy, unstructured free-text clinical notes into strict Pydantic JSON schemas.
2.  **Deterministic Code Mapping Phase**: Automatically maps the extracted symptoms and requested procedures to exact ICD-10 and CPT codes (e.g., `M54.5` for Low Back Pain).
3.  **Symbolic Evaluation Layer**: Deterministic Python rules evaluate the extracted facts against payer policies (e.g., Aetna vs. BCBS). The symbolic layer has the final say—the AI cannot override it.
4.  **Audit Trace Generation**: Every step of the pipeline is packaged into a traceable JSON `AuditTrace` object and saved to the SQLite Database.

---

## 👥 Multi-Role Web Portals

The application features a modern, Single-Page Application (SPA) dashboard with three distinct entry points:

1.  **👨‍⚕️ Doctor Portal**: Submit patient clinical notes, evaluate payer policies, and catch "Red Flags" before filing claims. Automatically generates a unique `Patient Code` upon submission.
2.  **👤 Patient Portal**: Patients log in via their mobile number to view a history of their doctor visits, requested procedures, and check if their insurance pre-authorization is "Approved", "Blocked", or "Pending".
3.  **🏛️ Insurer Portal**: Insurers log in and search securely for patient reports using a `Patient Code`. They can review the AI's "Readiness Score", the denial simulation, and the full audit trace.

---

## 🚀 Getting Started

### 1. Prerequisites
*   Python 3.9 or higher
*   An active [Groq API Key](https://console.groq.com/keys)

### 2. Installation
Clone the repository and install the required dependencies:
```bash
git clone https://github.com/yourusername/medi-guard-ai.git
cd medi-guard-ai
pip install -r requirements.txt
```

### 3. Environment Variables
You must set your Groq API key in your environment. You can place an `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### 4. Running the Server
Start the FastAPI application using Uvicorn:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start at `http://localhost:8000`.

---

## 🧭 How to Use

1. Open `http://localhost:8000` in your web browser.
2. **Setup a Demo Account**: Under the **Doctor** tab, click **"Register new Doctor"** to create a test profile.
3. **Submit a Claim**: 
    - Log in to the Doctor Portal.
    - Fill in a test Patient Name and Mobile Number.
    - Click **"📄 Strong Case"** or **"📄 Weak Case"** to load a pre-filled clinical note.
    - Click **⚡ Run Pre-Adjudication**.
4. **Get the Patient Code**: The system will evaluate the note, save it to the SQLite database, generate a `Patient Code` (e.g., `PT-A1B2C3`), and show you the pre-adjudication results (including the 3D graph!).
5. **Simulate the Insurer**: Log out, go to the **Insurer** tab, register an account, and search for that exact `Patient Code` to view the claim!

---

## 📂 Repository Structure

```text
medi-guard-ai/
├── app/
│   ├── main.py               # FastAPI entrypoint, HTTP REST endpoints, & DB sessions
│   ├── database.py           # SQLite connection and session factory
│   ├── models.py             # SQLAlchemy ORM definitions for Users and Reports
│   ├── policy_engine.py      # Symbolic rule engine & insurance compliance configs
│   ├── llm_extractor.py      # LLM interfacing module via Groq
│   ├── schemas.py            # Pydantic typing & Pipeline schema structures
│   └── static/               # Frontend Assets
│       ├── index.html        # App UI Shell
│       ├── app.js            # SPA Routing & 3D Graph Render Logic
│       └── style.css         # Custom Design System
├── requirements.txt
└── README.md
```

---

## 📸 Screenshots

*(Add your screenshots here by dragging and dropping them into GitHub)*
*   *Screenshot 1: The 3D Evidence Graph*
*   *Screenshot 2: The Insurer Search Dashboard*
*   *Screenshot 3: The Denial Simulation Results*

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
<div align="center">
  
# 🛡️ Medi-Guard AI

**The Neuro-Symbolic Prior Authorization & Pre-Adjudication Engine**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/release/python-390/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.103.2-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Groq API](https://img.shields.io/badge/Groq%20Llama%203-Powered-f3f4f6?logo=groq)](https://groq.com)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=flat&logo=sqlite&logoColor=white)](https://sqlite.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

*Eliminate healthcare claim denials before they happen.*

---

[Key Features](#-key-features) • [Architecture](#%EF%B8%8F-neuro-symbolic-architecture) • [Portals](#-multi-role-web-portals) • [Installation](#-getting-started) • [Usage](#-how-to-use) • [Screenshots](#-screenshots)

</div>

## 📖 Overview

**Medi-Guard AI** is an advanced, neuro-symbolic engine designed to automatically evaluate raw clinical notes against strict insurance payer rules *before* claims are submitted.

By combining the natural language understanding of Large Language Models (LLMs) with the absolute, deterministic reasoning of a symbolic Python rule engine, Medi-Guard AI **eliminates AI hallucinations** in the final decision-making process. The result is a fully auditable pipeline that tells doctors exactly *why* a claim might be denied and exactly *how* to fix it.

---

## 🌟 Key Features

*   **🛡️ Hallucination-Free Adjudication**: Neural networks extract facts (symptoms, durations), while a hard-coded symbolic logic engine enforces the insurance policies.
*   **📊 3D Evidence Graph Visualization**: An interactive, physics-based 3D graph visualizes exactly which clinical facts support or violate which policy clauses.
*   **🔧 Auto-Remediation Plans**: Automatically generates actionable next steps (e.g., "Complete 2 more weeks of Physical Therapy") if a claim evaluates poorly.
*   **🏥 Multi-Role Authentication**: Distinct dashboards and workflows for **Doctors**, **Insurers**, and **Patients**.
*   **💼 Secure Claim Linking**: Automatically generates unique, secure `Patient Codes` (e.g., `PT-A1B2C3`) that tie claims directly to anonymous searching for insurers.

---

## ⚙️ Neuro-Symbolic Architecture

Medi-Guard uses a **Pipeline-Driven** architecture consisting of distinct layers:

1.  **Neural Extraction Layer**: Uses Groq (`llama-3.3-70b-versatile`) to extract symptoms, duration parameters, medications, and treatments tried from noisy, unstructured free-text clinical notes into strict Pydantic JSON schemas.
2.  **Deterministic Code Mapping Phase**: Automatically maps the extracted symptoms and requested procedures to exact ICD-10 and CPT codes (e.g., `M54.5` for Low Back Pain).
3.  **Symbolic Evaluation Layer**: Deterministic Python rules evaluate the extracted facts against payer policies (e.g., Aetna vs. BCBS). The symbolic layer has the final say—the AI cannot override it.
4.  **Audit Trace Generation**: Every step of the pipeline is packaged into a traceable JSON `AuditTrace` object and saved to the SQLite Database.

---

## 👥 Multi-Role Web Portals

The application features a modern, Single-Page Application (SPA) dashboard with three distinct entry points:

1.  **👨‍⚕️ Doctor Portal**: Submit patient clinical notes, evaluate payer policies, and catch "Red Flags" before filing claims. Automatically generates a unique `Patient Code` upon submission.
2.  **👤 Patient Portal**: Patients log in via their mobile number to view a history of their doctor visits, requested procedures, and check if their insurance pre-authorization is "Approved", "Blocked", or "Pending".
3.  **🏛️ Insurer Portal**: Insurers log in and search securely for patient reports using a `Patient Code`. They can review the AI's "Readiness Score", the denial simulation, and the full audit trace.

---

## 🚀 Getting Started

### 1. Prerequisites
*   Python 3.9 or higher
*   An active [Groq API Key](https://console.groq.com/keys)

### 2. Installation
Clone the repository and install the required dependencies:
```bash
git clone https://github.com/yourusername/medi-guard-ai.git
cd medi-guard-ai
pip install -r requirements.txt
```

### 3. Environment Variables
You must set your Groq API key in your environment. You can place an `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### 4. Running the Server
Start the FastAPI application using Uvicorn:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start at `http://localhost:8000`.

---

## 🧭 How to Use

1. Open `http://localhost:8000` in your web browser.
2. **Setup a Demo Account**: Under the **Doctor** tab, click **"Register new Doctor"** to create a test profile.
3. **Submit a Claim**: 
    - Log in to the Doctor Portal.
    - Fill in a test Patient Name and Mobile Number.
    - Click **"📄 Strong Case"** or **"📄 Weak Case"** to load a pre-filled clinical note.
    - Click **⚡ Run Pre-Adjudication**.
4. **Get the Patient Code**: The system will evaluate the note, save it to the SQLite database, generate a `Patient Code` (e.g., `PT-A1B2C3`), and show you the pre-adjudication results (including the 3D graph!).
5. **Simulate the Insurer**: Log out, go to the **Insurer** tab, register an account, and search for that exact `Patient Code` to view the claim!

---

## 📂 Repository Structure

```text
medi-guard-ai/
├── app/
│   ├── main.py               # FastAPI entrypoint, HTTP REST endpoints, & DB sessions
│   ├── database.py           # SQLite connection and session factory
│   ├── models.py             # SQLAlchemy ORM definitions for Users and Reports
│   ├── policy_engine.py      # Symbolic rule engine & insurance compliance configs
│   ├── llm_extractor.py      # LLM interfacing module via Groq
│   ├── schemas.py            # Pydantic typing & Pipeline schema structures
│   └── static/               # Frontend Assets
│       ├── index.html        # App UI Shell
│       ├── app.js            # SPA Routing & 3D Graph Render Logic
│       └── style.css         # Custom Design System
├── requirements.txt
└── README.md
```

---

## 📸 Screenshots

*(Add your screenshots here by dragging and dropping them into GitHub)*
*   *Screenshot 1: The 3D Evidence Graph*
*   *Screenshot 2: The Insurer Search Dashboard*
*   *Screenshot 3: The Denial Simulation Results*

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
<div align="center">
  
# 🛡️ Medi-Guard AI

**The Neuro-Symbolic Prior Authorization & Pre-Adjudication Engine**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/release/python-390/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.103.2-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Groq API](https://img.shields.io/badge/Groq%20Llama%203-Powered-f3f4f6?logo=groq)](https://groq.com)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=flat&logo=sqlite&logoColor=white)](https://sqlite.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

*Eliminate healthcare claim denials before they happen.*

---

[Key Features](#-key-features) • [Architecture](#%EF%B8%8F-neuro-symbolic-architecture) • [Portals](#-multi-role-web-portals) • [Installation](#-getting-started) • [Usage](#-how-to-use) • [Screenshots](#-screenshots)

</div>

## 📖 Overview

**Medi-Guard AI** is an advanced, neuro-symbolic engine designed to automatically evaluate raw clinical notes against strict insurance payer rules *before* claims are submitted.

By combining the natural language understanding of Large Language Models (LLMs) with the absolute, deterministic reasoning of a symbolic Python rule engine, Medi-Guard AI **eliminates AI hallucinations** in the final decision-making process. The result is a fully auditable pipeline that tells doctors exactly *why* a claim might be denied and exactly *how* to fix it.

---

## 🌟 Key Features

*   **🛡️ Hallucination-Free Adjudication**: Neural networks extract facts (symptoms, durations), while a hard-coded symbolic logic engine enforces the insurance policies.
*   **📊 3D Evidence Graph Visualization**: An interactive, physics-based 3D graph visualizes exactly which clinical facts support or violate which policy clauses.
*   **🔧 Auto-Remediation Plans**: Automatically generates actionable next steps (e.g., "Complete 2 more weeks of Physical Therapy") if a claim evaluates poorly.
*   **🏥 Multi-Role Authentication**: Distinct dashboards and workflows for **Doctors**, **Insurers**, and **Patients**.
*   **💼 Secure Claim Linking**: Automatically generates unique, secure `Patient Codes` (e.g., `PT-A1B2C3`) that tie claims directly to anonymous searching for insurers.

---

## ⚙️ Neuro-Symbolic Architecture

Medi-Guard uses a **Pipeline-Driven** architecture consisting of distinct layers:

1.  **Neural Extraction Layer**: Uses Groq (`llama-3.3-70b-versatile`) to extract symptoms, duration parameters, medications, and treatments tried from noisy, unstructured free-text clinical notes into strict Pydantic JSON schemas.
2.  **Deterministic Code Mapping Phase**: Automatically maps the extracted symptoms and requested procedures to exact ICD-10 and CPT codes (e.g., `M54.5` for Low Back Pain).
3.  **Symbolic Evaluation Layer**: Deterministic Python rules evaluate the extracted facts against payer policies (e.g., Aetna vs. BCBS). The symbolic layer has the final say—the AI cannot override it.
4.  **Audit Trace Generation**: Every step of the pipeline is packaged into a traceable JSON `AuditTrace` object and saved to the SQLite Database.

---

## 👥 Multi-Role Web Portals

The application features a modern, Single-Page Application (SPA) dashboard with three distinct entry points:

1.  **👨‍⚕️ Doctor Portal**: Submit patient clinical notes, evaluate payer policies, and catch "Red Flags" before filing claims. Automatically generates a unique `Patient Code` upon submission.
2.  **👤 Patient Portal**: Patients log in via their mobile number to view a history of their doctor visits, requested procedures, and check if their insurance pre-authorization is "Approved", "Blocked", or "Pending".
3.  **🏛️ Insurer Portal**: Insurers log in and search securely for patient reports using a `Patient Code`. They can review the AI's "Readiness Score", the denial simulation, and the full audit trace.

---

## 🚀 Getting Started

### 1. Prerequisites
*   Python 3.9 or higher
*   An active [Groq API Key](https://console.groq.com/keys)

### 2. Installation
Clone the repository and install the required dependencies:
```bash
git clone https://github.com/yourusername/medi-guard-ai.git
cd medi-guard-ai
pip install -r requirements.txt
```

### 3. Environment Variables
You must set your Groq API key in your environment. You can place an `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### 4. Running the Server
Start the FastAPI application using Uvicorn:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start at `http://localhost:8000`.

---

## 🧭 How to Use

1. Open `http://localhost:8000` in your web browser.
2. **Setup a Demo Account**: Under the **Doctor** tab, click **"Register new Doctor"** to create a test profile.
3. **Submit a Claim**: 
    - Log in to the Doctor Portal.
    - Fill in a test Patient Name and Mobile Number.
    - Click **"📄 Strong Case"** or **"📄 Weak Case"** to load a pre-filled clinical note.
    - Click **⚡ Run Pre-Adjudication**.
4. **Get the Patient Code**: The system will evaluate the note, save it to the SQLite database, generate a `Patient Code` (e.g., `PT-A1B2C3`), and show you the pre-adjudication results (including the 3D graph!).
5. **Simulate the Insurer**: Log out, go to the **Insurer** tab, register an account, and search for that exact `Patient Code` to view the claim!

---

## 📂 Repository Structure

```text
medi-guard-ai/
├── app/
│   ├── main.py               # FastAPI entrypoint, HTTP REST endpoints, & DB sessions
│   ├── database.py           # SQLite connection and session factory
│   ├── models.py             # SQLAlchemy ORM definitions for Users and Reports
│   ├── policy_engine.py      # Symbolic rule engine & insurance compliance configs
│   ├── llm_extractor.py      # LLM interfacing module via Groq
│   ├── schemas.py            # Pydantic typing & Pipeline schema structures
│   └── static/               # Frontend Assets
│       ├── index.html        # App UI Shell
│       ├── app.js            # SPA Routing & 3D Graph Render Logic
│       └── style.css         # Custom Design System
├── requirements.txt
└── README.md
```

---

## 📸 Screenshots

*(Add your screenshots here by dragging and dropping them into GitHub)*
*   *Screenshot 1: The 3D Evidence Graph*
*   *Screenshot 2: The Insurer Search Dashboard*
*   *Screenshot 3: The Denial Simulation Results*

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
<div align="center">
  
# 🛡️ Medi-Guard AI

**The Neuro-Symbolic Prior Authorization & Pre-Adjudication Engine**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/release/python-390/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.103.2-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Groq API](https://img.shields.io/badge/Groq%20Llama%203-Powered-f3f4f6?logo=groq)](https://groq.com)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=flat&logo=sqlite&logoColor=white)](https://sqlite.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

*Eliminate healthcare claim denials before they happen.*

---

[Key Features](#-key-features) • [Architecture](#%EF%B8%8F-neuro-symbolic-architecture) • [Portals](#-multi-role-web-portals) • [Installation](#-getting-started) • [Usage](#-how-to-use) • [Screenshots](#-screenshots)

</div>

## 📖 Overview

**Medi-Guard AI** is an advanced, neuro-symbolic engine designed to automatically evaluate raw clinical notes against strict insurance payer rules *before* claims are submitted.

By combining the natural language understanding of Large Language Models (LLMs) with the absolute, deterministic reasoning of a symbolic Python rule engine, Medi-Guard AI **eliminates AI hallucinations** in the final decision-making process. The result is a fully auditable pipeline that tells doctors exactly *why* a claim might be denied and exactly *how* to fix it.

---

## 🌟 Key Features

*   **🛡️ Hallucination-Free Adjudication**: Neural networks extract facts (symptoms, durations), while a hard-coded symbolic logic engine enforces the insurance policies.
*   **📊 3D Evidence Graph Visualization**: An interactive, physics-based 3D graph visualizes exactly which clinical facts support or violate which policy clauses.
*   **🔧 Auto-Remediation Plans**: Automatically generates actionable next steps (e.g., "Complete 2 more weeks of Physical Therapy") if a claim evaluates poorly.
*   **🏥 Multi-Role Authentication**: Distinct dashboards and workflows for **Doctors**, **Insurers**, and **Patients**.
*   **💼 Secure Claim Linking**: Automatically generates unique, secure `Patient Codes` (e.g., `PT-A1B2C3`) that tie claims directly to anonymous searching for insurers.

---

## ⚙️ Neuro-Symbolic Architecture

Medi-Guard uses a **Pipeline-Driven** architecture consisting of distinct layers:

1.  **Neural Extraction Layer**: Uses Groq (`llama-3.3-70b-versatile`) to extract symptoms, duration parameters, medications, and treatments tried from noisy, unstructured free-text clinical notes into strict Pydantic JSON schemas.
2.  **Deterministic Code Mapping Phase**: Automatically maps the extracted symptoms and requested procedures to exact ICD-10 and CPT codes (e.g., `M54.5` for Low Back Pain).
3.  **Symbolic Evaluation Layer**: Deterministic Python rules evaluate the extracted facts against payer policies (e.g., Aetna vs. BCBS). The symbolic layer has the final say—the AI cannot override it.
4.  **Audit Trace Generation**: Every step of the pipeline is packaged into a traceable JSON `AuditTrace` object and saved to the SQLite Database.

---

## 👥 Multi-Role Web Portals

The application features a modern, Single-Page Application (SPA) dashboard with three distinct entry points:

1.  **👨‍⚕️ Doctor Portal**: Submit patient clinical notes, evaluate payer policies, and catch "Red Flags" before filing claims. Automatically generates a unique `Patient Code` upon submission.
2.  **👤 Patient Portal**: Patients log in via their mobile number to view a history of their doctor visits, requested procedures, and check if their insurance pre-authorization is "Approved", "Blocked", or "Pending".
3.  **🏛️ Insurer Portal**: Insurers log in and search securely for patient reports using a `Patient Code`. They can review the AI's "Readiness Score", the denial simulation, and the full audit trace.

---

## 🚀 Getting Started

### 1. Prerequisites
*   Python 3.9 or higher
*   An active [Groq API Key](https://console.groq.com/keys)

### 2. Installation
Clone the repository and install the required dependencies:
```bash
git clone https://github.com/yourusername/medi-guard-ai.git
cd medi-guard-ai
pip install -r requirements.txt
```

### 3. Environment Variables
You must set your Groq API key in your environment. You can place an `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### 4. Running the Server
Start the FastAPI application using Uvicorn:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start at `http://localhost:8000`.

---

## 🧭 How to Use

1. Open `http://localhost:8000` in your web browser.
2. **Setup a Demo Account**: Under the **Doctor** tab, click **"Register new Doctor"** to create a test profile.
3. **Submit a Claim**: 
    - Log in to the Doctor Portal.
    - Fill in a test Patient Name and Mobile Number.
    - Click **"📄 Strong Case"** or **"📄 Weak Case"** to load a pre-filled clinical note.
    - Click **⚡ Run Pre-Adjudication**.
4. **Get the Patient Code**: The system will evaluate the note, save it to the SQLite database, generate a `Patient Code` (e.g., `PT-A1B2C3`), and show you the pre-adjudication results (including the 3D graph!).
5. **Simulate the Insurer**: Log out, go to the **Insurer** tab, register an account, and search for that exact `Patient Code` to view the claim!

---

## 📂 Repository Structure

```text
medi-guard-ai/
├── app/
│   ├── main.py               # FastAPI entrypoint, HTTP REST endpoints, & DB sessions
│   ├── database.py           # SQLite connection and session factory
│   ├── models.py             # SQLAlchemy ORM definitions for Users and Reports
│   ├── policy_engine.py      # Symbolic rule engine & insurance compliance configs
│   ├── llm_extractor.py      # LLM interfacing module via Groq
│   ├── schemas.py            # Pydantic typing & Pipeline schema structures
│   └── static/               # Frontend Assets
│       ├── index.html        # App UI Shell
│       ├── app.js            # SPA Routing & 3D Graph Render Logic
│       └── style.css         # Custom Design System
├── requirements.txt
└── README.md
```

---

## 📸 Screenshots

*(Add your screenshots here by dragging and dropping them into GitHub)*
*   *Screenshot 1: The 3D Evidence Graph*
*   *Screenshot 2: The Insurer Search Dashboard*
*   *Screenshot 3: The Denial Simulation Results*

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
