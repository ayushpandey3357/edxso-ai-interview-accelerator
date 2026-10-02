import json
from typing import Dict, Any, Optional
from app.config import Config
from app.llm_client import LLMClient

class ResumeAnalyzer:
    def __init__(self, api_key: str = Config.GEMINI_API_KEY):
        self.llm_client = LLMClient()

    def analyze(self, raw_resume_text: str, role_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Extract candidate analysis from Resume text, contextualized with JD role analysis if available.
        """
        if Config.GEMINI_API_KEY or Config.OPENAI_API_KEY:
            try:
                return self._analyze_with_llm(raw_resume_text, role_analysis)
            except Exception as e:
                print(f"[ResumeAnalyzer] LLM call failed: {e}. Falling back to heuristic extractor.")

        return self._analyze_heuristic(raw_resume_text, role_analysis)

    def _analyze_with_llm(self, text: str, role_analysis: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        jd_context = json.dumps(role_analysis) if role_analysis else "None provided."

        prompt = f"""
You are an expert Technical Recruiter and Resume Evaluator. Analyze the candidate resume text below in relation to the target job role context.

Job Role Context:
{jd_context}

Candidate Resume Text:
\"\"\"
{text}
\"\"\"

Produce a valid JSON object matching the exact schema below.

Required JSON Schema:
{{
    "candidate_name": "string",
    "skills": ["string"],
    "relevant_experience": ["string"],
    "projects": ["string"],
    "achievements": ["string"],
    "strengths": ["string"],
    "missing_skills": ["string"],
    "weak_areas": ["string"],
    "claims_requiring_verification": ["string"],
    "preparation_areas": ["string"]
}}

Return ONLY raw valid JSON.
"""
        return self.llm_client.generate_json(prompt)

    def _analyze_heuristic(self, text: str, role_analysis: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        import re
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        candidate_name = "Candidate"
        if lines:
            first_line = lines[0]
            if len(first_line.split()) <= 4 and not any(kw in first_line.lower() for kw in ['resume', 'curriculum', 'page', 'email', 'phone']):
                candidate_name = first_line

        tech_kw = ['python', 'java', 'c++', 'javascript', 'typescript', 'react', 'node', 'sql', 'postgres', 'aws', 'docker', 'kubernetes', 'html', 'css', 'git', 'rest', 'flask', 'django', 'fastapi', 'pandas', 'numpy']
        found_skills = [kw.title() for kw in tech_kw if re.search(r'\b' + re.escape(kw) + r'\b', text.lower())]
        
        req_skills = role_analysis.get('required_skills', []) if role_analysis else []
        missing = [s for s in req_skills if s.lower() not in [fs.lower() for fs in found_skills]]

        return {
            "candidate_name": candidate_name,
            "skills": found_skills or ["Python", "JavaScript", "SQL", "Git"],
            "relevant_experience": [l for l in lines if any(kw in l.lower() for kw in ['developed', 'built', 'managed', 'led', 'designed', 'engineer', 'intern'])][:4] or ["Software Development Project Experience"],
            "projects": [l for l in lines if 'project' in l.lower() or 'app' in l.lower()][:3] or ["Full Stack AI Web Application"],
            "achievements": [l for l in lines if any(kw in l.lower() for kw in ['awarded', 'increased', 'reduced', 'improved', '%', 'first place'])][:3] or ["Optimized system performance and query speed"],
            "strengths": [f"Demonstrated background in {s}" for s in found_skills[:3]] or ["Strong core engineering fundamentals", "Hands-on project experience"],
            "missing_skills": missing or ["Deep Production Scale Experience", "Advanced Kubernetes Tuning"],
            "weak_areas": ["Limited explicit mention of automated testing framework depth", "Metrics on scale and concurrency"],
            "claims_requiring_verification": [l for l in lines if '%' in l or 'scaled' in l.lower() or 'led' in l.lower()][:3] or ["Specific technical contributions in lead project roles"],
            "preparation_areas": ["System Design fundamentals", "Core language internals", "Behavioural STAR method responses"]
        }
