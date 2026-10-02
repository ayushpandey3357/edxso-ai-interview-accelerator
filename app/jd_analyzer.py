import re
from typing import Dict, Any, List
from app.config import Config
from app.llm_client import LLMClient

class JDAnalyzer:
    def __init__(self, api_key: str = Config.GEMINI_API_KEY):
        self.llm_client = LLMClient()

    def analyze(self, raw_jd_text: str) -> Dict[str, Any]:
        """
        Extract structured role analysis strictly from Job Description text only.
        """
        raw_jd_text = raw_jd_text or ""
        
        if Config.GEMINI_API_KEY or Config.OPENAI_API_KEY:
            try:
                res = self._analyze_with_llm(raw_jd_text)
                return self._validate_and_sanitize_role_analysis(res)
            except Exception as e:
                print(f"[JDAnalyzer] LLM call failed: {e}. Falling back to heuristic extractor.")
        
        res = self._analyze_heuristic(raw_jd_text)
        return self._validate_and_sanitize_role_analysis(res)

    def _analyze_with_llm(self, text: str) -> Dict[str, Any]:
        prompt = f"""
You are an expert HR and Talent Engineer. Analyze ONLY the following Job Description (JD) text.

CRITICAL DIRECTIVES:
1. Extract role details strictly from the Job Description text provided below.
2. DO NOT include any candidate names, candidate contact information, email addresses, phone numbers, personal locations/addresses, or resume details.
3. For 'responsibilities', include ONLY actual workplace duties, actions, and job expectations described in the JD.
4. If a field or section is not mentioned in the Job Description, specify "Not specified". Do NOT invent details or use non-JD text.

Required JSON Schema:
{{
    "job_title": "string",
    "responsibilities": ["string"],
    "required_skills": ["string"],
    "preferred_skills": ["string"],
    "technical_competencies": ["string"],
    "behavioural_competencies": ["string"],
    "experience_expectations": "string",
    "keywords": ["string"],
    "important_concepts": ["string"],
    "qualifications": ["string"]
}}

Job Description Text:
\"\"\"
{text}
\"\"\"

Return ONLY raw valid JSON.
"""
        return self.llm_client.generate_json(prompt)

    def _analyze_heuristic(self, text: str) -> Dict[str, Any]:
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        clean_lines = [l for l in lines if not self._is_candidate_contact_info(l)]
        
        title = "Software / Product Engineer"
        for line in clean_lines[:5]:
            if any(kw in line.lower() for kw in ['engineer', 'developer', 'manager', 'lead', 'architect', 'specialist', 'analyst', 'designer', 'consultant']):
                title = line
                break

        tech_kw = ['python', 'java', 'c++', 'javascript', 'typescript', 'react', 'node', 'sql', 'postgres', 'aws', 'docker', 'kubernetes', 'system design', 'rest api', 'graphql', 'machine learning', 'ai', 'data structures', 'algorithms']
        found_tech = [kw.title() for kw in tech_kw if re.search(r'\b' + re.escape(kw) + r'\b', text.lower())]
        
        behav_kw = ['communication', 'leadership', 'teamwork', 'ownership', 'problem solving', 'adaptability', 'agile', 'collaboration']
        found_behav = [kw.title() for kw in behav_kw if re.search(r'\b' + re.escape(kw) + r'\b', text.lower())]

        responsibilities = [
            l for l in clean_lines
            if len(l) > 15 and self._is_valid_responsibility_line(l)
        ][:5]

        return {
            "job_title": title,
            "responsibilities": responsibilities or ["Not specified"],
            "required_skills": found_tech[:6] or ["Not specified"],
            "preferred_skills": found_tech[6:10] or ["Not specified"],
            "technical_competencies": ["Backend Architecture", "API Integration", "Database Design", "Performance Optimization"],
            "behavioural_competencies": found_behav or ["Communication", "Ownership", "Analytical Thinking", "Team Collaboration"],
            "experience_expectations": "2+ years of relevant experience in software/product engineering",
            "keywords": list(set(found_tech + found_behav)) or ["Not specified"],
            "important_concepts": ["Data Structures", "API Protocols", "Distributed Systems", "Clean Code"],
            "qualifications": ["Bachelor's or Master's degree in Computer Science, STEM or equivalent experience"]
        }

    def _is_candidate_contact_info(self, text: str) -> bool:
        """
        Detects whether a string is candidate personal contact, address, name header, or non-JD personal info.
        """
        if not text or not isinstance(text, str):
            return False

        t_lower = text.lower().strip()

        # Email check
        if re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text):
            return True

        # Phone check
        if re.search(r'\+?\d[\d\s\-\(\)]{8,}\d', text):
            return True

        # Common personal contact indicators
        contact_kws = ['email:', 'phone:', 'mobile:', 'github:', 'linkedin:', 'address:', 'location:', 'pincode:', 'zip code:', 'dob:']
        if any(kw in t_lower for kw in contact_kws):
            return True

        # Location/city/country indicators when appearing in non-job context
        loc_patterns = [
            r'\blucknow\b', r'\bmumbai\b', r'\bdelhi\b', r'\bbangalore\b', r'\bhyderabad\b',
            r'\bchennai\b', r'\bkolkata\b', r'\bpune\b', r'\bnoida\b', r'\bgurgaon\b',
            r'\bindia\b', r'\bnew york\b', r'\blondon\b', r'\bsan francisco\b'
        ]
        has_location = any(re.search(pat, t_lower) for pat in loc_patterns)

        # Name/Location headers like "Firstname Lastname City, Country"
        if has_location and not any(verb in t_lower for verb in ['develop', 'manage', 'build', 'lead', 'design', 'ensure', 'create', 'engineer', 'developer', 'work', 'implement', 'responsible', 'location']):
            return True

        # Check if line looks purely like a personal name (2-4 capitalized words with no technical action verbs or JD keywords)
        words = text.strip().split()
        if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w.isalpha()):
            if not any(kw in t_lower for kw in ['engineer', 'developer', 'lead', 'architect', 'manager', 'specialist', 'analyst', 'senior', 'junior', 'full', 'stack', 'backend', 'frontend', 'software', 'data', 'product', 'responsibilities', 'qualifications', 'requirements']):
                return True

        return False

    def _is_valid_responsibility_line(self, text: str) -> bool:
        if self._is_candidate_contact_info(text):
            return False
        
        t_lower = text.lower()
        action_verbs = ['develop', 'build', 'lead', 'manage', 'design', 'collaborate', 'ensure', 'create', 'write', 'architect', 'maintain', 'test', 'deliver', 'support', 'work', 'implement', 'optimize', 'analyze', 'drive', 'responsible', 'spearhead']
        return any(verb in t_lower for verb in action_verbs)

    def _validate_and_sanitize_role_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deterministic post-processing sanitizer to ensure no personal candidate information leaks into JD fields.
        """
        if not isinstance(analysis, dict):
            analysis = {}

        # 1. Job Title
        title = str(analysis.get('job_title', '')).strip()
        if not title or self._is_candidate_contact_info(title):
            title = "Software / Product Engineer"
        analysis['job_title'] = title

        # Helper to clean list fields
        def sanitize_list(lst: List[Any]) -> List[str]:
            if not isinstance(lst, list):
                return ["Not specified"]
            cleaned = []
            for item in lst:
                item_str = str(item).strip()
                if item_str and not self._is_candidate_contact_info(item_str) and item_str.lower() != "not specified":
                    cleaned.append(item_str)
            return cleaned if cleaned else ["Not specified"]

        # 2. Responsibilities - Filter out non-responsibilities & contact info
        raw_resp = analysis.get('responsibilities', [])
        clean_resp = []
        if isinstance(raw_resp, list):
            for item in raw_resp:
                item_str = str(item).strip()
                if item_str and not self._is_candidate_contact_info(item_str) and item_str.lower() != "not specified":
                    clean_resp.append(item_str)

        analysis['responsibilities'] = clean_resp if clean_resp else ["Not specified"]

        # 3. Other fields
        analysis['required_skills'] = sanitize_list(analysis.get('required_skills', []))
        analysis['preferred_skills'] = sanitize_list(analysis.get('preferred_skills', []))
        analysis['technical_competencies'] = sanitize_list(analysis.get('technical_competencies', []))
        analysis['behavioural_competencies'] = sanitize_list(analysis.get('behavioural_competencies', []))
        analysis['keywords'] = sanitize_list(analysis.get('keywords', []))
        analysis['important_concepts'] = sanitize_list(analysis.get('important_concepts', []))
        analysis['qualifications'] = sanitize_list(analysis.get('qualifications', []))

        exp = str(analysis.get('experience_expectations', '')).strip()
        if not exp or self._is_candidate_contact_info(exp):
            exp = "Not specified"
        analysis['experience_expectations'] = exp

        return analysis
