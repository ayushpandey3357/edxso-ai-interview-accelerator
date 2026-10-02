# EDXSO AI Interview Accelerator ⚡

An AI-powered personalized interview platform built for Assignment 3. The platform analyzes Job Descriptions (JDs) and Candidate Resumes to compute deterministic Job Fit, dynamically conduct a 3-Level Voice AI Interview, generate granular Performance Reports, and craft personalized Preparation Plans.

---

## 🌟 Core Features

1. **Role Analysis (JD)**
   - JD text paste or file upload (`.pdf`, `.docx`, `.txt`).
   - Extracts: Job Title, Responsibilities, Required Skills, Preferred Skills, Technical & Behavioural Competencies, Experience Expectations, Keywords, Concepts, and Qualifications.

2. **Candidate Analysis (Resume)**
   - Resume paste or file upload (`.pdf`, `.docx`, `.txt`).
   - Extracts: Skills, Relevant Experience, Projects, Achievements, Strengths, Missing Skills, Weak Areas, Claims Requiring Verification, and Preparation Areas.

3. **Deterministic & Explainable Job Fit Matrix**
   - 4-Tier Weighted Formula: Skill Match (40%), Experience Alignment (30%), Competency Coverage (20%), Qualifications (10%).
   - Provides clear breakdown of Strong Matches, Partial Matches, and Missing/Weak Areas.

4. **3-Level Adaptive AI Voice Interview Engine**
   - **Level 1: Screening** (Resume, Motivation, Basic understanding, Role fit, Communication, Experience, Career goals).
   - **Level 2: Competency** (Technical understanding, Problem solving, Projects, Behavioural competencies, Decision making, Practical application).
   - **Level 3: Deep Dive** (Technical depth, Why/How architectural choices, Challenge vague answers, Probe resume claims, Scenarios, Counter questions, Identify inconsistencies).
   - **Dynamic Question Generation**: Questions adapt in real-time based on JD, Resume, previous turns, detected strengths/weaknesses, and candidate answers. No fixed question lists!
   - **Voice Engine**: AI Text-to-Speech (TTS) audio playback + Live Speech-to-Text (STT) browser voice input.

5. **Granular Performance Report**
   - Overall Score, Role Fit, Technical Knowledge, Problem Solving, Communication, Confidence, Depth of Understanding, Behavioural Fit.
   - Interactive Plotly Radar Chart & Question-by-Question breakdown.

6. **Actionable Preparation Plan**
   - Prioritized focus topics with concrete study items and recommended learning resources.
   - Project drills, STAR behavioral guidelines, and recommended mock practice questions.

---

## 🏗️ Architecture & Project Structure

```text
edxso-ai-interview-accelerator/
├── app/
│   ├── __init__.py
│   ├── config.py             # Configuration & environment variable loading
│   ├── database.py           # SQLite database layer & CRUD operations
│   ├── document_parser.py    # PDF, DOCX, TXT document parser
│   ├── jd_analyzer.py        # Role requirements & competency extraction
│   ├── resume_analyzer.py    # Candidate resume profile & claims analyzer
│   ├── job_fit.py            # Deterministic job fit matrix calculator
│   ├── interview_engine.py   # 3-Level adaptive interview orchestrator
│   ├── question_generator.py # Dynamic contextual LLM question generator
│   ├── answer_evaluator.py  # Real-time answer evaluation engine
│   ├── voice.py              # TTS and STT voice engine
│   ├── report_generator.py   # Performance analytics & report generator
│   └── preparation.py        # Personalized preparation plan generator
├── dashboard/
│   ├── __init__.py
│   └── app.py                # Streamlit multi-page interactive web UI
├── data/                     # SQLite database storage directory
├── tests/
│   ├── __init__.py
│   ├── test_database.py      # Database CRUD unit tests
│   ├── test_analyzers.py     # Analyzer & Fit matrix unit tests
│   └── test_interview_engine.py # Interview engine unit tests
├── run.py                    # Application startup entry script
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore                # Git exclusions
└── README.md                 # Project documentation
```

---

## 🗄️ SQLite Database Schema

- `job_descriptions`: Stores raw JD text, title, and extracted role analysis JSON.
- `resumes`: Stores raw resume text, candidate name, and extracted candidate profile JSON.
- `job_fits`: Stores calculated fit score, dimension breakdown, and match lists.
- `interview_sessions`: Tracks active/completed sessions, JD ID, Resume ID, and current level.
- `interview_turns`: Stores turns, question numbers, questions, audio paths, candidate answer transcripts, and evaluations.
- `performance_reports`: Stores final aggregate scores, radar chart metrics, and question-level feedback.
- `preparation_plans`: Stores prioritized study topics, learning materials, and practice drills.

---

## 🚀 Quick Start Guide

### 1. Clone & Setup Virtual Environment
```bash
git clone <repository-url>
cd edxso-ai-interview-accelerator
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(Optional)* Add your `GEMINI_API_KEY` or `OPENAI_API_KEY` to `.env`. If no API key is provided, the platform operates in offline heuristic mode seamlessly.

### 4. Run the Web Application
```bash
python run.py
```
Or run directly via Streamlit:
```bash
streamlit run dashboard/app.py
```

### 5. Run Automated Tests
```bash
pytest tests/
```

---

## 🛡️ License
Built for EDXSO AI Product Engineer Intern Assignment 3.
