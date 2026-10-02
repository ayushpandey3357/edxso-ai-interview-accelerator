import os
import tempfile
import pytest
from app.database import Database

@pytest.fixture
def temp_db():
    tmp_dir = tempfile.mkdtemp()
    db_path = os.path.join(tmp_dir, "test.db")
    db = Database(db_path=db_path)
    yield db
    try:
        if os.path.exists(db_path):
            os.unlink(db_path)
    except Exception:
        pass

def test_jd_crud(temp_db):
    role_analysis = {
        "job_title": "Senior Backend Engineer",
        "required_skills": ["Python", "PostgreSQL", "Docker"]
    }
    jd_id = temp_db.save_jd("Senior Backend Engineer", "Raw JD content...", role_analysis)
    assert jd_id > 0

    fetched = temp_db.get_jd(jd_id)
    assert fetched is not None
    assert fetched['title'] == "Senior Backend Engineer"
    assert fetched['role_analysis']['required_skills'] == ["Python", "PostgreSQL", "Docker"]

def test_resume_crud(temp_db):
    cand_analysis = {
        "candidate_name": "Jane Doe",
        "skills": ["Python", "FastAPI", "PostgreSQL"]
    }
    res_id = temp_db.save_resume("Jane Doe", "Raw Resume content...", cand_analysis)
    assert res_id > 0

    fetched = temp_db.get_resume(res_id)
    assert fetched is not None
    assert fetched['candidate_name'] == "Jane Doe"

def test_interview_session_flow(temp_db):
    jd_id = temp_db.save_jd("Engineer", "JD text", {})
    res_id = temp_db.save_resume("Candidate", "Resume text", {})
    
    sess_id = temp_db.create_interview_session(jd_id, res_id)
    assert sess_id > 0

    turn_id = temp_db.add_interview_turn(sess_id, level=1, question_number=1, question_text="Tell me about yourself?", question_focus="Background")
    assert turn_id > 0

    eval_data = {"score": 85, "feedback": "Good answer"}
    temp_db.update_turn_answer(turn_id, "I am a software engineer with 5 years experience.", eval_data)

    turns = temp_db.get_session_turns(sess_id)
    assert len(turns) == 1
    assert turns[0]['answer_text'] == "I am a software engineer with 5 years experience."
    assert turns[0]['evaluation']['score'] == 85
