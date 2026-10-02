import sqlite3
import json
import os
from typing import Dict, Any, List, Optional
from app.config import Config

class Database:
    def __init__(self, db_path: str = Config.DB_PATH):
        self.db_path = db_path
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Job Descriptions table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_descriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                raw_text TEXT NOT NULL,
                role_analysis_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Resumes table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_name TEXT,
                raw_text TEXT NOT NULL,
                candidate_analysis_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Job Fit table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_fits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jd_id INTEGER NOT NULL,
                resume_id INTEGER NOT NULL,
                fit_score REAL NOT NULL,
                fit_details_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (jd_id) REFERENCES job_descriptions (id),
                FOREIGN KEY (resume_id) REFERENCES resumes (id)
            )
            """)

            # Interview Sessions table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS interview_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jd_id INTEGER NOT NULL,
                resume_id INTEGER NOT NULL,
                current_level INTEGER DEFAULT 1,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (jd_id) REFERENCES job_descriptions (id),
                FOREIGN KEY (resume_id) REFERENCES resumes (id)
            )
            """)

            # Interview Turns (Questions & Answers) table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS interview_turns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                level INTEGER NOT NULL,
                question_number INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                question_focus TEXT,
                audio_path TEXT,
                answer_text TEXT,
                evaluation_json TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES interview_sessions (id)
            )
            """)

            # Performance Reports table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                overall_score REAL NOT NULL,
                report_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES interview_sessions (id)
            )
            """)

            # Preparation Plans table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS preparation_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                plan_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES interview_sessions (id)
            )
            """)

            conn.commit()

    # CRUD Helpers
    def save_jd(self, title: str, raw_text: str, role_analysis: Dict[str, Any]) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO job_descriptions (title, raw_text, role_analysis_json) VALUES (?, ?, ?)",
                (title, raw_text, json.dumps(role_analysis))
            )
            conn.commit()
            return cursor.lastrowid

    def get_jd(self, jd_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM job_descriptions WHERE id = ?", (jd_id,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d['role_analysis'] = json.loads(d['role_analysis_json']) if d['role_analysis_json'] else {}
                return d
            return None

    def update_jd_analysis(self, jd_id: int, title: str, role_analysis: Dict[str, Any]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE job_descriptions SET title = ?, role_analysis_json = ? WHERE id = ?",
                (title, json.dumps(role_analysis), jd_id)
            )
            conn.commit()


    def save_resume(self, candidate_name: str, raw_text: str, candidate_analysis: Dict[str, Any]) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO resumes (candidate_name, raw_text, candidate_analysis_json) VALUES (?, ?, ?)",
                (candidate_name, raw_text, json.dumps(candidate_analysis))
            )
            conn.commit()
            return cursor.lastrowid

    def get_resume(self, resume_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d['candidate_analysis'] = json.loads(d['candidate_analysis_json']) if d['candidate_analysis_json'] else {}
                return d
            return None

    def save_job_fit(self, jd_id: int, resume_id: int, fit_score: float, fit_details: Dict[str, Any]) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO job_fits (jd_id, resume_id, fit_score, fit_details_json) VALUES (?, ?, ?, ?)",
                (jd_id, resume_id, fit_score, json.dumps(fit_details))
            )
            conn.commit()
            return cursor.lastrowid

    def get_latest_job_fit(self, jd_id: int, resume_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM job_fits WHERE jd_id = ? AND resume_id = ? ORDER BY id DESC LIMIT 1",
                (jd_id, resume_id)
            )
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d['fit_details'] = json.loads(d['fit_details_json']) if d['fit_details_json'] else {}
                return d
            return None

    def create_interview_session(self, jd_id: int, resume_id: int) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO interview_sessions (jd_id, resume_id, current_level, status) VALUES (?, ?, 1, 'active')",
                (jd_id, resume_id)
            )
            conn.commit()
            return cursor.lastrowid

    def get_interview_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM interview_sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_session_level(self, session_id: int, new_level: int, status: str = 'active'):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE interview_sessions SET current_level = ?, status = ? WHERE id = ?",
                (new_level, status, session_id)
            )
            conn.commit()

    def add_interview_turn(self, session_id: int, level: int, question_number: int, question_text: str, question_focus: str = "") -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO interview_turns (session_id, level, question_number, question_text, question_focus) VALUES (?, ?, ?, ?, ?)",
                (session_id, level, question_number, question_text, question_focus)
            )
            conn.commit()
            return cursor.lastrowid

    def update_turn_answer(self, turn_id: int, answer_text: str, evaluation: Dict[str, Any], audio_path: str = ""):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE interview_turns SET answer_text = ?, evaluation_json = ?, audio_path = ? WHERE id = ?",
                (answer_text, json.dumps(evaluation), audio_path, turn_id)
            )
            conn.commit()

    def get_session_turns(self, session_id: int) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM interview_turns WHERE session_id = ? ORDER BY id ASC", (session_id,))
            rows = cursor.fetchall()
            turns = []
            for row in rows:
                d = dict(row)
                d['evaluation'] = json.loads(d['evaluation_json']) if d['evaluation_json'] else {}
                turns.append(d)
            return turns

    def save_performance_report(self, session_id: int, overall_score: float, report_json: Dict[str, Any]) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO performance_reports (session_id, overall_score, report_json) VALUES (?, ?, ?)",
                (session_id, overall_score, json.dumps(report_json))
            )
            conn.commit()
            return cursor.lastrowid

    def get_performance_report(self, session_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM performance_reports WHERE session_id = ? ORDER BY id DESC LIMIT 1", (session_id,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d['report'] = json.loads(d['report_json']) if d['report_json'] else {}
                return d
            return None

    def save_preparation_plan(self, session_id: int, plan_json: Dict[str, Any]) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO preparation_plans (session_id, plan_json) VALUES (?, ?)",
                (session_id, json.dumps(plan_json))
            )
            conn.commit()
            return cursor.lastrowid

    def get_preparation_plan(self, session_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM preparation_plans WHERE session_id = ? ORDER BY id DESC LIMIT 1", (session_id,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d['plan'] = json.loads(d['plan_json']) if d['plan_json'] else {}
                return d
            return None
