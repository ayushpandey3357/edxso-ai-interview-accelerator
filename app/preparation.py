import json
from typing import Dict, Any
from app.config import Config
from app.llm_client import LLMClient

class PreparationPlanner:
    def __init__(self, api_key: str = Config.GEMINI_API_KEY):
        self.llm_client = LLMClient()

    def generate_plan(
        self,
        report_data: Dict[str, Any],
        role_analysis: Dict[str, Any],
        candidate_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generates a prioritized personalized preparation plan with concrete topics, study materials, and practice tasks.
        """
        if Config.GEMINI_API_KEY or Config.OPENAI_API_KEY:
            try:
                return self._generate_with_llm(report_data, role_analysis, candidate_analysis)
            except Exception as e:
                print(f"[PreparationPlanner] LLM preparation plan generation failed: {e}. Falling back to deterministic plan.")

        return self._generate_deterministic(report_data, role_analysis, candidate_analysis)

    def _generate_with_llm(
        self,
        report: Dict[str, Any],
        role: Dict[str, Any],
        candidate: Dict[str, Any]
    ) -> Dict[str, Any]:
        prompt = f"""
You are a Senior Career & Engineering Preparation Coach. Create a personalized, actionable Preparation Plan for the candidate aiming for the position: {role.get('job_title')}.

INTERVIEW PERFORMANCE & GAPS:
Overall Score: {report.get('overall_score')}/100
Weaknesses Identified: {', '.join(report.get('weaknesses', []))}
Preparation Gaps: {', '.join(report.get('preparation_gaps', []))}
Missing Skills from JD: {', '.join(candidate.get('missing_skills', []))}
Required Skills for Role: {', '.join(role.get('required_skills', []))}

Output a valid JSON object matching the exact schema below:
{{
    "title": "string",
    "summary": "string",
    "prioritized_topics": [
        {{
            "priority": "High" | "Medium" | "Low",
            "topic": "string",
            "why_important": "string",
            "concrete_study_items": ["string"],
            "recommended_resources": ["string"]
        }}
    ],
    "actionable_projects_or_drills": ["string"],
    "behavioural_star_strategy": ["string"],
    "recommended_mock_questions": ["string"]
}}

Return ONLY raw valid JSON.
"""
        return self.llm_client.generate_json(prompt)

    def _generate_deterministic(
        self,
        report: Dict[str, Any],
        role: Dict[str, Any],
        candidate: Dict[str, Any]
    ) -> Dict[str, Any]:
        job_title = role.get('job_title', 'Software/Product Engineer')
        missing_skills = candidate.get('missing_skills', [])

        topics = []
        if missing_skills:
            topics.append({
                "priority": "High",
                "topic": f"Master Core Required Skills: {', '.join(missing_skills[:2])}",
                "why_important": "These skills were specified in the Job Description but showed gaps during resume analysis or interview turns.",
                "concrete_study_items": [
                    f"Study architectural patterns and best practices for {missing_skills[0] if missing_skills else 'System Design'}.",
                    "Implement a mini project incorporating these technologies with proper error handling."
                ],
                "recommended_resources": [
                    f"Official documentation and deep dive tutorials for {missing_skills[0] if missing_skills else 'the framework'}.",
                    "High Performance Engineering Case Studies (GitHub / Engineering Blogs)."
                ]
            })

        topics.append({
            "priority": "High",
            "topic": "System Design, Scalability & Trade-offs",
            "why_important": "Level 3 Deep Dive identified opportunities to explain technical choices with more granular architectural justification.",
            "concrete_study_items": [
                "Practice explaining database indexing, caching strategies (Redis), and asynchronous queues (Celery/RabbitMQ).",
                "Prepare quantitative numbers (e.g. latency targets, throughput, memory footprints) for your major past projects."
            ],
            "recommended_resources": [
                "Designing Data-Intensive Applications (Martin Kleppmann)",
                "System Design Primer (GitHub Repository)"
            ]
        })

        topics.append({
            "priority": "Medium",
            "topic": "Behavioural STAR Method Refinement (Situation, Task, Action, Result)",
            "why_important": "Ensures responses demonstrate leadership, ownership, and measurable business impact during Level 1 Screening and Level 2 Competency.",
            "concrete_study_items": [
                "Draft 3 STAR stories highlighting conflict resolution, technical trade-offs, and unexpected system outages.",
                "Quantify results (e.g. 'reduced latency by 35%' or 'improved query response time from 1.2s to 150ms')."
            ],
            "recommended_resources": [
                "The STAR Method Handbook for Engineering Candidates",
                "Amazon Leadership Principles & Engineering Case Studies"
            ]
        })

        return {
            "title": f"Targeted Preparation Plan for {job_title}",
            "summary": f"This plan focuses on bridging identified gaps from your interview assessment, emphasizing technical depth, system architecture, and concise communication.",
            "prioritized_topics": topics,
            "actionable_projects_or_drills": [
                f"Build a production-grade REST API backend using {role.get('required_skills', ['Python'])[0]} with full unit testing suite.",
                "Conduct a mock system design session whiteboarding microservices communication and latency optimization.",
                "Record 2-minute spoken summaries of your core projects to improve confidence and verbal clarity."
            ],
            "behavioural_star_strategy": [
                "Situation: Briefly set the context and technical stakes (max 20 seconds).",
                "Task: Specify your exact role and responsibility in the initiative.",
                "Action: Focus 60% of your answer on your specific choices, technical logic, and trade-offs.",
                "Result: Close with quantifiable business or performance impact metrics."
            ],
            "recommended_mock_questions": [
                f"How would you handle a sudden 10x traffic spike in your {job_title} application?",
                "Tell me about a time you made a technical trade-off under tight deadlines. What did you compromise and why?",
                "Explain the internal mechanics of memory management and database indexing in your primary language stack."
            ]
        }
