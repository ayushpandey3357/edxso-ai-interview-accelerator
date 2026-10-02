from typing import Dict, Any, List, Optional
from app.database import Database
from app.jd_analyzer import JDAnalyzer
from app.resume_analyzer import ResumeAnalyzer
from app.job_fit import JobFitAnalyzer
from app.question_generator import QuestionGenerator
from app.answer_evaluator import AnswerEvaluator
from app.voice import VoiceEngine

class InterviewEngine:
    QUESTIONS_PER_LEVEL = 2  # Default turns per level (Screening, Competency, Deep Dive)

    def __init__(self, db: Database, api_key: str = ""):
        self.db = db
        self.question_gen = QuestionGenerator(api_key=api_key)
        self.evaluator = AnswerEvaluator(api_key=api_key)
        self.voice_engine = VoiceEngine()

    def start_session(self, jd_id: int, resume_id: int) -> int:
        session_id = self.db.create_interview_session(jd_id, resume_id)
        # Generate initial question for Level 1, Question 1
        self.prepare_next_turn(session_id)
        return session_id

    def get_session_state(self, session_id: int) -> Dict[str, Any]:
        session = self.db.get_interview_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found.")

        jd = self.db.get_jd(session['jd_id'])
        resume = self.db.get_resume(session['resume_id'])
        job_fit = self.db.get_latest_job_fit(session['jd_id'], session['resume_id'])
        turns = self.db.get_session_turns(session_id)

        # Collect aggregate metrics
        scores = [t['evaluation'].get('score', 0) for t in turns if t.get('evaluation')]
        avg_score = round(sum(scores) / max(1, len(scores)), 1) if scores else 0.0

        all_strengths = []
        all_weaknesses = []
        for t in turns:
            ev = t.get('evaluation', {})
            all_strengths.extend(ev.get('strengths', []))
            all_weaknesses.extend(ev.get('weaknesses', []))

        # Check pending question
        pending_turn = None
        if turns and turns[-1]['answer_text'] is None:
            pending_turn = turns[-1]

        return {
            "session_id": session_id,
            "current_level": session['current_level'],
            "status": session['status'],
            "jd": jd,
            "resume": resume,
            "job_fit": job_fit,
            "turns": turns,
            "pending_turn": pending_turn,
            "average_score": avg_score,
            "accumulated_strengths": list(dict.fromkeys(all_strengths)),
            "accumulated_weaknesses": list(dict.fromkeys(all_weaknesses))
        }

    def prepare_next_turn(self, session_id: int) -> Optional[Dict[str, Any]]:
        state = self.get_session_state(session_id)
        if state['status'] == 'completed':
            return None

        # Check if there is already an unanswered turn pending
        if state['pending_turn']:
            return state['pending_turn']

        turns = state['turns']
        current_level = state['current_level']

        # Determine level turn count
        level_turns = [t for t in turns if t['level'] == current_level]
        if len(level_turns) >= self.QUESTIONS_PER_LEVEL:
            if current_level < 3:
                current_level += 1
                self.db.update_session_level(session_id, current_level, 'active')
                state['current_level'] = current_level
            else:
                self.db.update_session_level(session_id, 3, 'completed')
                return None

        # Generate question
        q_data = self.question_gen.generate_next_question(
            level=current_level,
            role_analysis=state['jd']['role_analysis'],
            candidate_analysis=state['resume']['candidate_analysis'],
            previous_turns=turns,
            detected_strengths=state['accumulated_strengths'],
            detected_weaknesses=state['accumulated_weaknesses'],
            unresolved_claims=state['resume']['candidate_analysis'].get('claims_requiring_verification', [])
        )

        q_number = len(turns) + 1
        turn_id = self.db.add_interview_turn(
            session_id=session_id,
            level=current_level,
            question_number=q_number,
            question_text=q_data['question'],
            question_focus=q_data.get('focus', 'General Competency')
        )

        return {
            "id": turn_id,
            "session_id": session_id,
            "level": current_level,
            "question_number": q_number,
            "question_text": q_data['question'],
            "question_focus": q_data.get('focus', 'General Competency')
        }

    def submit_answer(self, session_id: int, turn_id: int, answer_text: str, audio_bytes: Optional[bytes] = None) -> Dict[str, Any]:
        state = self.get_session_state(session_id)
        
        # If voice audio provided but answer_text empty, attempt transcription
        if audio_bytes and not answer_text.strip():
            transcribed = self.voice_engine.transcribe_audio_bytes(audio_bytes)
            if transcribed:
                answer_text = transcribed

        # Find target turn
        target_turn = None
        for t in state['turns']:
            if t['id'] == turn_id:
                target_turn = t
                break

        if not target_turn:
            raise ValueError(f"Turn {turn_id} not found in session.")

        # Evaluate Answer
        eval_result = self.evaluator.evaluate_answer(
            question_text=target_turn['question_text'],
            question_focus=target_turn.get('question_focus', ''),
            answer_text=answer_text,
            level=target_turn['level'],
            role_analysis=state['jd']['role_analysis'],
            candidate_analysis=state['resume']['candidate_analysis']
        )

        # Save turn update in DB
        self.db.update_turn_answer(
            turn_id=turn_id,
            answer_text=answer_text,
            evaluation=eval_result,
            audio_path=""
        )

        # Check if session completed after this turn
        updated_turns = self.db.get_session_turns(session_id)
        if len(updated_turns) >= (self.QUESTIONS_PER_LEVEL * 3):
            self.db.update_session_level(session_id, 3, 'completed')

        return eval_result
