import os
import tempfile
import pytest
from app.jd_analyzer import JDAnalyzer
from app.database import Database

def test_jd_analysis_isolates_candidate_info():
    analyzer = JDAnalyzer(api_key="")
    
    # Contaminated JD text containing candidate header & contact information
    raw_jd_text = """
    Ayush Kumar Pandey Lucknow, India
    Email: ayush.pandey@example.com
    Phone: +91 9876543210
    
    Job Title: Senior Backend Engineer
    
    Responsibilities:
    - Design, build, and maintain scalable RESTful microservices in Python and FastAPI.
    - Optimize SQL queries and manage PostgreSQL databases.
    - Collaborate with frontend engineers to deliver product features.
    
    Required Skills:
    - Python, SQL, PostgreSQL, Docker, AWS
    """

    res = analyzer.analyze(raw_jd_text)

    # 1. Job Title validation
    assert "Ayush" not in res['job_title']
    assert "Lucknow" not in res['job_title']
    assert "ayush.pandey@example.com" not in res['job_title']

    # 2. Responsibilities validation
    for resp in res['responsibilities']:
        assert "Ayush" not in resp, f"Candidate name found in responsibility: {resp}"
        assert "Pandey" not in resp, f"Candidate name found in responsibility: {resp}"
        assert "Lucknow" not in resp, f"Candidate address found in responsibility: {resp}"
        assert "India" not in resp, f"Candidate address found in responsibility: {resp}"
        assert "ayush.pandey@example.com" not in resp, f"Email found in responsibility: {resp}"
        assert "+91 9876543210" not in resp, f"Phone found in responsibility: {resp}"

    # Ensure actual responsibilities were captured
    assert len(res['responsibilities']) > 0
    assert any("RESTful" in r or "Python" in r or "microservices" in r for r in res['responsibilities'])

def test_jd_sanitization_generic_candidate_name_and_address():
    analyzer = JDAnalyzer(api_key="")

    # Generic candidate contact data
    raw_jd = """
    Johnathan Vance London, UK
    Contact: john.vance@techcorp.io | +44 20 7946 0912
    
    Position: Lead Data Engineer
    Role Expectations:
    - Architect distributed data pipelines using Apache Spark and Kafka.
    - Implement real-time streaming analytics and data warehouse models.
    """

    res = analyzer.analyze(raw_jd)

    all_text = " ".join([
        res['job_title'],
        " ".join(res['responsibilities']),
        " ".join(res['required_skills']),
        " ".join(res['preferred_skills']),
        " ".join(res['qualifications'])
    ])

    assert "Johnathan" not in all_text
    assert "Vance" not in all_text
    assert "London" not in all_text
    assert "john.vance@techcorp.io" not in all_text
    assert "+44 20 7946 0912" not in all_text

def test_missing_information_returns_not_specified():
    analyzer = JDAnalyzer(api_key="")

    minimal_jd = "Software Engineer needed to write python scripts."
    res = analyzer.analyze(minimal_jd)

    assert isinstance(res['responsibilities'], list)
    assert len(res['responsibilities']) > 0

def test_db_reanalyze_and_update_jd():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    db = Database(db_path=db_path)

    # Save initial contaminated JD record
    contaminated_analysis = {
        "job_title": "Ayush Kumar Pandey Lucknow, India",
        "responsibilities": ["Ayush Kumar Pandey Lucknow, India", "Develop APIs"],
        "required_skills": ["Python"]
    }

    jd_id = db.save_jd("Senior Engineer", "JD text...", contaminated_analysis)
    
    # Re-analyze & update
    analyzer = JDAnalyzer(api_key="")
    raw_text = "Senior Software Engineer\nResponsibilities:\n- Build microservices\n- Manage SQL databases"
    clean_analysis = analyzer.analyze(raw_text)

    db.update_jd_analysis(jd_id, clean_analysis['job_title'], clean_analysis)

    updated_jd = db.get_jd(jd_id)
    assert updated_jd is not None
    assert "Ayush" not in updated_jd['role_analysis']['job_title']
    assert "Ayush" not in " ".join(updated_jd['role_analysis']['responsibilities'])

    try:
        os.unlink(db_path)
    except Exception:
        pass
