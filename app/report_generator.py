import json
from typing import Dict, Any
from app.config import Config
from app.llm_client import LLMClient

class ReportGenerator:
    def __init__(self, api_key: str = Config.GEMINI_API_KEY):
        self.llm_client = LLMClient()

    def generate_report(
        self,
        session_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generates comprehensive performance report based on interview turns and job fit.
        """
        if Config.GEMINI_API_KEY or Config.OPENAI_API_KEY:
            try:
                return self._generate_with_llm(session_state)
            except Exception as e:
                print(f"[ReportGenerator] LLM report generation failed: {e}. Falling back to deterministic generator.")

        return self._generate_deterministic(session_state)

    def _generate_with_llm(self, state: Dict[str, Any]) -> Dict[str, Any]:
        turns_summary = []
        for t in state.get('turns', []):
            q = t.get('question_text')
            a = t.get('answer_text', 'No answer')
            ev = t.get('evaluation', {})
            turns_summary.append(f"Level {t.get('level')} Q: {q}\nA: {a}\nEval: {json.dumps(ev)}")

        prompt = f"""
You are an Executive Technical Assessment Director. Generate a comprehensive Interview Performance Report for the candidate based on the complete interview trajectory below.

JOB TITLE: {state.get('jd', {}).get('title')}
JOB FIT SCORE: {state.get('job_fit', {}).get('fit_score')}%

INTERVIEW TURNS & EVALUATIONS:
{chr(10).join(turns_summary)}

Produce a valid JSON object matching the exact schema below:
{{
    "overall_score": number (0-100),
    "role_fit": number (0-100),
    "technical_knowledge": number (0-100),
    "problem_solving": number (0-100),
    "communication": number (0-100),
    "confidence": number (0-100),
    "depth_of_understanding": number (0-100),
    "behavioural_fit": number (0-100),
    "strengths": ["string"],
    "weaknesses": ["string"],
    "preparation_gaps": ["string"],
    "interview_readiness": "string (e.g. Strong Hire, Ready with minor prep, Needs targeted preparation, Not ready)",
    "executive_summary": "string",
    "question_feedback": [
        {{
            "question_number": number,
            "level": number,
            "question": "string",
            "candidate_answer": "string",
            "score": number,
            "feedback": "string",
            "key_takeaway": "string"
        }}
    ]
}}

Return ONLY raw valid JSON.
"""
        return self.llm_client.generate_json(prompt)

    def _generate_deterministic(self, state: Dict[str, Any]) -> Dict[str, Any]:
        turns = state.get('turns', [])
        job_fit = state.get('job_fit', {})
        fit_score = job_fit.get('fit_score', 75.0)

        evals = [t.get('evaluation', {}) for t in turns if t.get('evaluation')]
        
        if evals:
            tech = sum(e.get('technical_knowledge', 75) for e in evals) / len(evals)
            depth = sum(e.get('depth_of_understanding', 70) for e in evals) / len(evals)
            prob = sum(e.get('problem_solving', 75) for e in evals) / len(evals)
            comm = sum(e.get('communication', 80) for e in evals) / len(evals)
            conf = sum(e.get('confidence', 80) for e in evals) / len(evals)
            behav = sum(e.get('behavioural_fit', 78) for e in evals) / len(evals)
            turn_overall = sum(e.get('score', 75) for e in evals) / len(evals)
        else:
            tech = depth = prob = comm = conf = behav = turn_overall = 70.0

        overall = round((fit_score * 0.35) + (turn_overall * 0.65), 1)

        readiness = "Needs Targeted Preparation"
        if overall >= 85:
            readiness = "Strong Hire / Fully Ready"
        elif overall >= 75:
            readiness = "Ready with Minor Refinements"
        elif overall >= 65:
            readiness = "Moderate Readiness - Needs Technical Deep Dives"

        all_strengths = []
        all_weaknesses = []
        question_feedback = []

        for idx, t in enumerate(turns):
            ev = t.get('evaluation', {})
            all_strengths.extend(ev.get('strengths', []))
            all_weaknesses.extend(ev.get('weaknesses', []))
            question_feedback.append({
                "question_number": t.get('question_number', idx + 1),
                "level": t.get('level', 1),
                "question": t.get('question_text', ''),
                "candidate_answer": t.get('answer_text', 'No answer provided'),
                "score": ev.get('score', 0),
                "feedback": ev.get('feedback', 'No detailed feedback.'),
                "key_takeaway": ev.get('follow_up_recommendation', 'Refine answer specificity.')
            })

        prep_gaps = [w for w in list(dict.fromkeys(all_weaknesses)) if w]
        if not prep_gaps:
            prep_gaps = ["Practice edge-case system design questions", "Elaborate on production scale metrics"]

        return {
            "overall_score": overall,
            "role_fit": round(fit_score, 1),
            "technical_knowledge": round(tech, 1),
            "problem_solving": round(prob, 1),
            "communication": round(comm, 1),
            "confidence": round(conf, 1),
            "depth_of_understanding": round(depth, 1),
            "behavioural_fit": round(behav, 1),
            "strengths": list(dict.fromkeys(all_strengths)) or ["Demonstrated core technical understanding", "Good response structure"],
            "weaknesses": list(dict.fromkeys(all_weaknesses)) or ["Can enhance depth in architectural trade-offs"],
            "preparation_gaps": prep_gaps,
            "interview_readiness": readiness,
            "executive_summary": f"Candidate completed a 3-level assessment for {state.get('jd', {}).get('title', 'the role')}. Overall performance score is {overall}/100 with a role fit of {fit_score}%.",
            "question_feedback": question_feedback
        }
