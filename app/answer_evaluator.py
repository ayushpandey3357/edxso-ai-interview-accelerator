import json
from typing import Dict, Any
from app.config import Config
from app.llm_client import LLMClient

class AnswerEvaluator:
    def __init__(self, api_key: str = Config.GEMINI_API_KEY):
        self.llm_client = LLMClient()

    def evaluate_answer(
        self,
        question_text: str,
        question_focus: str,
        answer_text: str,
        level: int,
        role_analysis: Dict[str, Any],
        candidate_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluates candidate answer real-time across technical, problem solving, communication, and confidence dimensions.
        """
        if not answer_text or not answer_text.strip():
            return {
                "score": 0,
                "technical_knowledge": 0,
                "depth_of_understanding": 0,
                "problem_solving": 0,
                "communication": 0,
                "confidence": 0,
                "behavioural_fit": 0,
                "strengths": [],
                "weaknesses": ["No answer or transcript recorded."],
                "feedback": "No answer was provided by the candidate.",
                "follow_up_recommendation": "Re-prompt candidate for input."
            }

        if Config.GEMINI_API_KEY or Config.OPENAI_API_KEY:
            try:
                return self._evaluate_with_llm(
                    question_text, question_focus, answer_text, level, role_analysis, candidate_analysis
                )
            except Exception as e:
                print(f"[AnswerEvaluator] LLM evaluation failed: {e}. Falling back to heuristic evaluator.")

        return self._evaluate_heuristic(
            question_text, question_focus, answer_text, level, role_analysis, candidate_analysis
        )

    def _evaluate_with_llm(
        self,
        question_text: str,
        question_focus: str,
        answer_text: str,
        level: int,
        role_analysis: Dict[str, Any],
        candidate_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        prompt = f"""
You are a Lead Hiring Manager & Technical Interviewer evaluating a candidate's answer.

INTERVIEW CONTEXT:
Level: {level}
Question Asked: \"{question_text}\"
Question Focus: \"{question_focus}\"
Candidate Answer Transcript: \"{answer_text}\"

Target Job Title: {role_analysis.get('job_title')}
Target Skills: {', '.join(role_analysis.get('required_skills', []))}

Evaluate the candidate's answer thoroughly and return a valid JSON matching this schema:
{{
    "score": number (0-100),
    "technical_knowledge": number (0-100),
    "depth_of_understanding": number (0-100),
    "problem_solving": number (0-100),
    "communication": number (0-100),
    "confidence": number (0-100),
    "behavioural_fit": number (0-100),
    "strengths": ["string"],
    "weaknesses": ["string"],
    "feedback": "string",
    "follow_up_recommendation": "string"
}}

Return ONLY raw valid JSON.
"""
        return self.llm_client.generate_json(prompt)

    def _evaluate_heuristic(
        self,
        question_text: str,
        question_focus: str,
        answer_text: str,
        level: int,
        role_analysis: Dict[str, Any],
        candidate_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        words = answer_text.strip().split()
        word_count = len(words)

        if word_count < 15:
            base_score = 45.0
            depth = 35.0
            comm = 50.0
            weakness = ["Answer is very brief and lacks technical specifics."]
        elif word_count < 40:
            base_score = 70.0
            depth = 65.0
            comm = 75.0
            weakness = ["Could provide more concrete architecture or quantitative metrics."]
        else:
            base_score = 85.0
            depth = 85.0
            comm = 88.0
            weakness = []

        req_skills = [s.lower() for s in role_analysis.get('required_skills', [])]
        matched_kw = [s.title() for s in req_skills if s in answer_text.lower()]
        
        tech_score = min(100.0, base_score + (len(matched_kw) * 5))
        prob_score = min(100.0, base_score + (5 if any(kw in answer_text.lower() for kw in ['because', 'solved', 'architecture', 'metric', 'result', 'trade-off']) else 0))
        conf_score = min(100.0, base_score + (5 if any(kw in answer_text.lower() for kw in ['led', 'built', 'designed', 'responsible', 'achieved']) else 0))
        behav_score = min(100.0, base_score)

        overall = round((tech_score + depth + prob_score + comm + conf_score + behav_score) / 6, 1)

        strengths = []
        if matched_kw:
            strengths.append(f"Demonstrated terminology in: {', '.join(matched_kw)}")
        if word_count >= 30:
            strengths.append("Articulate response with good structural flow.")
        if not strengths:
            strengths.append("Addressed the prompt directly.")

        return {
            "score": overall,
            "technical_knowledge": round(tech_score, 1),
            "depth_of_understanding": round(depth, 1),
            "problem_solving": round(prob_score, 1),
            "communication": round(comm, 1),
            "confidence": round(conf_score, 1),
            "behavioural_fit": round(behav_score, 1),
            "strengths": strengths,
            "weaknesses": weakness or ["Can include more specific edge-case handling."],
            "feedback": f"The answer covers key aspects of {question_focus}. Word count: {word_count}. Score: {overall}/100.",
            "follow_up_recommendation": "Probe further into technical architecture or specific metric trade-offs."
        }
