import json
from typing import Dict, Any, List, Optional
from app.config import Config
from app.llm_client import LLMClient

class QuestionGenerator:
    def __init__(self, api_key: str = Config.GEMINI_API_KEY):
        self.llm_client = LLMClient()

    def generate_next_question(
        self,
        level: int,
        role_analysis: Dict[str, Any],
        candidate_analysis: Dict[str, Any],
        previous_turns: List[Dict[str, Any]],
        detected_strengths: Optional[List[str]] = None,
        detected_weaknesses: Optional[List[str]] = None,
        unresolved_claims: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Dynamically generates the next interview question tailored strictly to context.
        """
        if Config.GEMINI_API_KEY or Config.OPENAI_API_KEY:
            try:
                return self._generate_with_llm(
                    level, role_analysis, candidate_analysis, previous_turns,
                    detected_strengths, detected_weaknesses, unresolved_claims
                )
            except Exception as e:
                print(f"[QuestionGenerator] LLM call failed: {e}. Falling back to dynamic contextual generator.")

        return self._generate_dynamic_fallback(
            level, role_analysis, candidate_analysis, previous_turns,
            detected_strengths, detected_weaknesses, unresolved_claims
        )

    def _generate_with_llm(
        self,
        level: int,
        role_analysis: Dict[str, Any],
        candidate_analysis: Dict[str, Any],
        previous_turns: List[Dict[str, Any]],
        detected_strengths: Optional[List[str]],
        detected_weaknesses: Optional[List[str]],
        unresolved_claims: Optional[List[str]]
    ) -> Dict[str, Any]:
        level_descriptions = {
            1: "Level 1: Screening (Focus: Resume experience, career goals, motivation, basic understanding, role fit, communication)",
            2: "Level 2: Competency (Focus: Technical understanding, problem solving, projects, behavioural competencies, decision making, practical application)",
            3: "Level 3: Deep Dive (Focus: Technical depth, why/how architectural choices, challenging vague previous answers, probing resume claims, scenario edge-cases, identifying inconsistencies)"
        }

        history_summary = []
        for t in previous_turns:
            q = t.get('question_text', '')
            a = t.get('answer_text', 'No answer provided yet.')
            eval_info = t.get('evaluation', {})
            score = eval_info.get('score', 'N/A')
            weakness = eval_info.get('weaknesses', '')
            history_summary.append(f"Q: {q}\nA: {a}\nScore: {score}/100 | Feedback: {weakness}\n")

        history_str = "\n---\n".join(history_summary) if history_summary else "No previous questions asked yet."

        prompt = f"""
You are an expert, highly articulate Senior AI Interviewer conducting a real-time interview.

CURRENT STAGE:
{level_descriptions.get(level, level_descriptions[1])}

JOB DESCRIPTION CONTEXT:
Job Title: {role_analysis.get('job_title')}
Required Skills: {', '.join(role_analysis.get('required_skills', []))}
Responsibilities: {', '.join(role_analysis.get('responsibilities', [])[:3])}

CANDIDATE CONTEXT:
Candidate Name: {candidate_analysis.get('candidate_name', 'Candidate')}
Claimed Skills: {', '.join(candidate_analysis.get('skills', []))}
Key Projects: {', '.join(candidate_analysis.get('projects', [])[:2])}
Claims to Verify: {', '.join(unresolved_claims or candidate_analysis.get('claims_requiring_verification', []))}

INTERVIEW HISTORY SO FAR:
{history_str}

RECENT EVALUATION METRICS:
Detected Strengths: {', '.join(detected_strengths or [])}
Detected Weaknesses: {', '.join(detected_weaknesses or [])}

CRITICAL RULES:
1. Dynamically generate ONE single targeted interview question.
2. DO NOT repeat any previously asked question.
3. If the candidate gave a vague, incomplete, or weak answer in the previous turn, directly reference their response and ask for clarification, specifics, or technical depth (especially in Level 2 and Level 3).
4. If in Level 3, probe their specific resume claims or architectural decisions.
5. Provide a clear 'focus' field explaining what competency or claim this question tests.

Output a valid JSON object matching:
{{
    "question": "string",
    "focus": "string",
    "target_competency": "string"
}}

Return ONLY raw valid JSON.
"""
        return self.llm_client.generate_json(prompt)

    def _generate_dynamic_fallback(
        self,
        level: int,
        role_analysis: Dict[str, Any],
        candidate_analysis: Dict[str, Any],
        previous_turns: List[Dict[str, Any]],
        detected_strengths: Optional[List[str]],
        detected_weaknesses: Optional[List[str]],
        unresolved_claims: Optional[List[str]]
    ) -> Dict[str, Any]:
        turn_count = len(previous_turns)
        cand_name = candidate_analysis.get('candidate_name', 'Candidate')
        job_title = role_analysis.get('job_title', 'this role')
        skills = candidate_analysis.get('skills', ['engineering'])
        projects = candidate_analysis.get('projects', ['your previous projects'])
        claims = unresolved_claims or candidate_analysis.get('claims_requiring_verification', [])

        last_turn = previous_turns[-1] if previous_turns else None
        last_answer = last_turn.get('answer_text', '') if last_turn else ''
        last_eval = last_turn.get('evaluation', {}) if last_turn else {}

        if level == 1:
            if turn_count == 0:
                q = f"Welcome {cand_name}. To start our Level 1 Screening, could you walk me through your background and explain why you're interested in the {job_title} position?"
                focus = "Resume overview and motivation"
            elif turn_count == 1:
                skill_sample = skills[0] if skills else "software engineering"
                q = f"Thank you. You mentioned experience with {skill_sample}. How have you applied this skill in your recent roles or projects to deliver impact?"
                focus = "Core skill application & communication"
            else:
                q = f"What are your core career goals for the next 2 years, and how does this {job_title} role align with those aspirations?"
                focus = "Career alignment & expectations"
        elif level == 2:
            if last_eval and last_eval.get('score', 100) < 65:
                q = f"Following up on your previous answer, you touched on the general approach. Could you walk me through the step-by-step problem-solving process you used when building {projects[0] if projects else 'your application'}?"
                focus = "Problem solving clarification & depth"
            elif turn_count % 2 == 0:
                skill_req = role_analysis.get('required_skills', ['System Architecture'])[0]
                q = f"In Level 2 Competency, let's discuss {skill_req}. How do you design and optimize applications using {skill_req} to ensure scalability and reliability?"
                focus = f"Technical competency in {skill_req}"
            else:
                proj = projects[0] if projects else "your key project"
                q = f"Tell me about a complex technical decision or trade-off you had to make while working on {proj}. What were the alternatives and why did you choose that path?"
                focus = "Decision making & practical trade-offs"
        else: # Level 3 Deep Dive
            if claims and turn_count % 2 == 0:
                claim = claims[0]
                q = f"In Level 3 Deep Dive, we probe specific claims. You noted: '{claim}'. Could you explain the exact technical mechanism, metrics, and your individual contribution behind this achievement?"
                focus = "Probing resume claims & verification"
            elif last_answer and len(last_answer.split()) < 30:
                q = f"In your last response, your answer was quite brief. In a high-stakes scenario for a {job_title}, how would you handle unexpected performance bottlenecks under heavy load? Walk me through your step-by-step diagnostic strategy."
                focus = "Challenging vague responses & scenario depth"
            else:
                q = f"If we asked you to redesign the core architecture of one of your major projects to handle 100x traffic with sub-50ms latency, what bottlenecks would emerge and how would you re-architect it?"
                focus = "Deep architectural scenarios & technical limits"

        return {
            "question": q,
            "focus": focus,
            "target_competency": focus
        }
