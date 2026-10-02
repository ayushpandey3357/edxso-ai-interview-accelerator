import pytest
from app.jd_analyzer import JDAnalyzer
from app.resume_analyzer import ResumeAnalyzer
from app.job_fit import JobFitAnalyzer

def test_jd_analyzer_heuristic():
    analyzer = JDAnalyzer(api_key="")
    raw_jd = """
    Job Title: Senior Python Developer
    Responsibilities:
    - Build scalable REST APIs in Python and FastAPI
    - Work with PostgreSQL databases and Docker
    Required Skills: Python, SQL, Docker, FastAPI
    """
    res = analyzer.analyze(raw_jd)
    assert res['job_title'] != ""
    assert isinstance(res['required_skills'], list)
    assert len(res['required_skills']) > 0

def test_resume_analyzer_heuristic():
    analyzer = ResumeAnalyzer(api_key="")
    raw_resume = """
    Alex Smith
    Software Engineer with experience in Python, Django, SQL, and Git.
    Developed microservices serving 50k DAU.
    """
    res = analyzer.analyze(raw_resume)
    assert res['candidate_name'] != ""
    assert "Python" in res['skills']

def test_job_fit_calculator():
    role = {
        "required_skills": ["Python", "SQL", "Docker"],
        "preferred_skills": ["AWS"],
        "technical_competencies": ["Backend Architecture"]
    }
    candidate = {
        "skills": ["Python", "SQL"],
        "relevant_experience": ["Software Developer"],
        "projects": ["Built API"],
        "strengths": ["Strong Python backend development"],
        "claims_requiring_verification": []
    }
    fit = JobFitAnalyzer.calculate_fit(role, candidate)
    assert "fit_score" in fit
    assert 0 <= fit['fit_score'] <= 100
    assert len(fit['strong_matches']) > 0
