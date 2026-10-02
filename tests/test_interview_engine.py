import os
import tempfile
import pytest
from app.database import Database
from app.interview_engine import InterviewEngine

@pytest.fixture
def temp_engine():
    tmp_dir = tempfile.mkdtemp()
    db_path = os.path.join(tmp_dir, "test.db")
    db = Database(db_path=db_path)
    engine = InterviewEngine(db, api_key="")
    yield engine
    try:
        if os.path.exists(db_path):
            os.unlink(db_path)
    except Exception:
        pass

def test_interview_session_progression(temp_engine):
    role = {
        "job_title": "AI Product Engineer",
        "required_skills": ["Python", "Machine Learning"],
        "responsibilities": ["Build AI systems"]
    }
    candidate = {
        "candidate_name": "Taylor Swift",
        "skills": ["Python", "PyTorch"],
        "projects": ["NLP Model"],
        "claims_requiring_verification": ["Built scale model"]
    }
    
    jd_id = temp_engine.db.save_jd("AI Product Engineer", "Raw JD", role)
    res_id = temp_engine.db.save_resume("Taylor Swift", "Raw Resume", candidate)

    # Start Session
    sess_id = temp_engine.start_session(jd_id, res_id)
    assert sess_id > 0

    state = temp_engine.get_session_state(sess_id)
    assert state['current_level'] == 1
    assert state['pending_turn'] is not None

    # Answer Turn 1
    pending = state['pending_turn']
    eval_res = temp_engine.submit_answer(sess_id, pending['id'], "I am an AI engineer with strong Python background.")
    assert eval_res['score'] > 0

    # Next Turn
    state2 = temp_engine.get_session_state(sess_id)
    assert len(state2['turns']) == 1
