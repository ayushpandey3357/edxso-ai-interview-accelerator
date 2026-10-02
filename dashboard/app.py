import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import Config
from app.database import Database
from app.document_parser import DocumentParser
from app.jd_analyzer import JDAnalyzer
from app.resume_analyzer import ResumeAnalyzer
from app.job_fit import JobFitAnalyzer
from app.interview_engine import InterviewEngine
from app.report_generator import ReportGenerator
from app.preparation import PreparationPlanner
from app.voice import VoiceEngine

# Page Config
st.set_page_config(
    page_title="AI Interview Accelerator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #4F46E5, #9333EA, #EC4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        color: #9CA3AF;
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .stButton>button {
        background: linear-gradient(90deg, #4F46E5, #7C3AED);
        color: white;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4);
    }
    .badge-level {
        background: #312E81;
        color: #A5B4FC;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Core Services
@st.cache_resource
def get_db():
    return Database()

db = get_db()
jd_analyzer = JDAnalyzer()
resume_analyzer = ResumeAnalyzer()
interview_engine = InterviewEngine(db)
report_gen = ReportGenerator()
prep_planner = PreparationPlanner()
voice_engine = VoiceEngine()

# Session State Initializations
if 'active_jd_id' not in st.session_state:
    st.session_state.active_jd_id = None
if 'active_resume_id' not in st.session_state:
    st.session_state.active_resume_id = None
if 'active_session_id' not in st.session_state:
    st.session_state.active_session_id = None

# Sidebar Navigation
st.sidebar.markdown("## ⚡ AI Interview Accelerator")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigation Menu",
    [
        "🚀 Dashboard",
        "📋 Role Analysis (JD)",
        "👤 Candidate Analysis",
        "🎯 Job Fit Matrix",
        "🎙️ AI Voice Interview",
        "📊 Performance Report",
        "📚 Preparation Plan"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ System Status")
api_status = "🟢 Gemini Connected" if Config.GEMINI_API_KEY else "🟡 Heuristic Engine (Offline Mode)"
st.sidebar.info(api_status)
if st.session_state.active_session_id:
    st.sidebar.success(f"Active Session ID: #{st.session_state.active_session_id}")

# ---------------------------------------------------------
# PAGE 1: DASHBOARD
# ---------------------------------------------------------
if page == "🚀 Dashboard":
    st.markdown('<div class="main-title">AI Interview Accelerator Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Personalized, adaptive 3-level AI interview platform powered by JD & Resume intelligence.</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        with db.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM job_descriptions")
            count_jds = c.fetchone()[0]
        st.metric("Total JDs Analyzed", count_jds)
    with col2:
        with db.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM resumes")
            count_resumes = c.fetchone()[0]
        st.metric("Resumes Analyzed", count_resumes)
    with col3:
        with db.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM interview_sessions")
            count_sessions = c.fetchone()[0]
        st.metric("Interview Sessions", count_sessions)
    with col4:
        with db.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT AVG(overall_score) FROM performance_reports")
            val = c.fetchone()[0]
            avg_score = round(val, 1) if val else 0.0
        st.metric("Average Score", f"{avg_score}%")

    st.markdown("---")
    st.markdown("### 📌 Active Workspace Selection")
    
    col_a, col_b = st.columns(2)
    with col_a:
        with db.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT id, title FROM job_descriptions ORDER BY id DESC")
            jds = c.fetchall()
        
        jd_options = {f"#{r['id']} - {r['title']}": r['id'] for r in jds}
        if jd_options:
            selected_jd_str = st.selectbox("Select Active Job Description (JD):", list(jd_options.keys()))
            st.session_state.active_jd_id = jd_options[selected_jd_str]
        else:
            st.info("No JDs saved yet. Go to 'Role Analysis (JD)' tab to add one.")

    with col_b:
        with db.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT id, candidate_name FROM resumes ORDER BY id DESC")
            resumes = c.fetchall()
        
        resume_options = {f"#{r['id']} - {r['candidate_name']}": r['id'] for r in resumes}
        if resume_options:
            selected_res_str = st.selectbox("Select Active Candidate Resume:", list(resume_options.keys()))
            st.session_state.active_resume_id = resume_options[selected_res_str]
        else:
            st.info("No Resumes saved yet. Go to 'Candidate Analysis' tab to add one.")

    st.markdown("---")
    st.markdown("### 🏁 Quick Start Workflow")
    st.markdown("""
    1. **Role Analysis**: Input Job Description via paste or PDF/DOCX/TXT upload.
    2. **Candidate Analysis**: Input Resume via paste or file upload.
    3. **Job Fit**: View deterministic compatibility score & gap matrix.
    4. **AI Voice Interview**: Experience Level 1 (Screening) ➡️ Level 2 (Competency) ➡️ Level 3 (Deep Dive) with real voice audio & TTS!
    5. **Performance & Prep**: Review comprehensive report and custom preparation plan.
    """)

# ---------------------------------------------------------
# PAGE 2: ROLE ANALYSIS (JD)
# ---------------------------------------------------------
elif page == "📋 Role Analysis (JD)":
    st.markdown('<div class="main-title">Job Description Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Extract structured role requirements, competencies, responsibilities, and qualifications.</div>', unsafe_allow_html=True)

    input_mode = st.radio("Input Method:", ["Paste JD Text", "Upload File (.pdf, .docx, .txt)"], horizontal=True)
    
    jd_title_input = st.text_input("Job Title / Role Name:", "Senior Product / Software Engineer")
    raw_jd = ""

    if input_mode == "Paste JD Text":
        raw_jd = st.text_area("Paste Full Job Description Here:", height=220, placeholder="Paste job description requirements, responsibilities...")
    else:
        uploaded_jd = st.file_uploader("Upload JD Document:", type=["pdf", "docx", "txt"])
        if uploaded_jd:
            raw_jd = DocumentParser.parse_file(uploaded_jd.read(), uploaded_jd.name)
            st.success(f"Successfully extracted {len(raw_jd)} characters from {uploaded_jd.name}.")

    if st.button("Analyze Role & Save JD"):
        if not raw_jd.strip():
            st.error("Please provide Job Description text or upload a file.")
        else:
            with st.spinner("Analyzing Job Description with AI..."):
                analysis = jd_analyzer.analyze(raw_jd)
                jd_id = db.save_jd(jd_title_input or analysis.get('job_title', 'Role'), raw_jd, analysis)
                st.session_state.active_jd_id = jd_id
                st.success(f"Job Description saved successfully! (JD ID: #{jd_id})")

    if st.session_state.active_jd_id:
        st.markdown("---")
        jd_data = db.get_jd(st.session_state.active_jd_id)
        if jd_data:
            ra = jd_data['role_analysis']
            col_h1, col_h2 = st.columns([3, 1])
            with col_h1:
                st.markdown(f"### 📊 Structured Role Analysis: {jd_data['title']}")
            with col_h2:
                if st.button("🔄 Re-analyze & Sanitize"):
                    with st.spinner("Re-analyzing JD text and sanitizing role data..."):
                        clean_analysis = jd_analyzer.analyze(jd_data['raw_text'])
                        db.update_jd_analysis(jd_data['id'], clean_analysis.get('job_title', jd_data['title']), clean_analysis)
                        st.success("Re-analysis complete! Sanitized role data updated.")
                        st.rerun()



            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 🎯 Core Responsibilities")
                for r in ra.get('responsibilities', []):
                    st.markdown(f"- {r}")

                st.markdown("#### 🛠️ Required Technical Skills")
                st.write(", ".join([f"`{s}`" for s in ra.get('required_skills', [])]))

                st.markdown("#### 🌟 Preferred Skills")
                st.write(", ".join([f"`{s}`" for s in ra.get('preferred_skills', [])]))

            with col2:
                st.markdown("#### ⚙️ Technical Competencies")
                for c in ra.get('technical_competencies', []):
                    st.markdown(f"- {c}")

                st.markdown("#### 🤝 Behavioural Competencies")
                for b in ra.get('behavioural_competencies', []):
                    st.markdown(f"- {b}")

                st.markdown("#### 🎓 Qualifications & Experience")
                st.info(f"**Experience Expectations**: {ra.get('experience_expectations')}")
                for q in ra.get('qualifications', []):
                    st.markdown(f"- {q}")

# ---------------------------------------------------------
# PAGE 3: CANDIDATE ANALYSIS
# ---------------------------------------------------------
elif page == "👤 Candidate Analysis":
    st.markdown('<div class="main-title">Candidate Resume Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Extract candidate skills, experience, projects, strengths, missing areas, and claims to verify.</div>', unsafe_allow_html=True)

    input_mode_res = st.radio("Resume Input Method:", ["Paste Resume Text", "Upload Resume File (.pdf, .docx, .txt)"], horizontal=True)
    cand_name_input = st.text_input("Candidate Name:", "Alex Morgan")
    raw_resume = ""

    if input_mode_res == "Paste Resume Text":
        raw_resume = st.text_area("Paste Candidate Resume Content:", height=220, placeholder="Paste resume text...")
    else:
        uploaded_res = st.file_uploader("Upload Resume Document:", type=["pdf", "docx", "txt"])
        if uploaded_res:
            raw_resume = DocumentParser.parse_file(uploaded_res.read(), uploaded_res.name)
            st.success(f"Successfully extracted {len(raw_resume)} characters from {uploaded_res.name}.")

    if st.button("Analyze Resume & Save"):
        if not raw_resume.strip():
            st.error("Please provide Resume text or upload a file.")
        else:
            with st.spinner("Analyzing Resume with AI..."):
                active_jd = db.get_jd(st.session_state.active_jd_id) if st.session_state.active_jd_id else None
                role_ctx = active_jd['role_analysis'] if active_jd else None
                
                analysis = resume_analyzer.analyze(raw_resume, role_ctx)
                res_id = db.save_resume(cand_name_input or analysis.get('candidate_name', 'Candidate'), raw_resume, analysis)
                st.session_state.active_resume_id = res_id
                st.success(f"Candidate Resume saved successfully! (Resume ID: #{res_id})")

    if st.session_state.active_resume_id:
        st.markdown("---")
        res_data = db.get_resume(st.session_state.active_resume_id)
        if res_data:
            ca = res_data['candidate_analysis']
            st.markdown(f"### 👤 Candidate Profile: {res_data['candidate_name']}")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 💪 Verified Skills")
                st.write(", ".join([f"`{s}`" for s in ca.get('skills', [])]))

                st.markdown("#### 💼 Relevant Experience Highlights")
                for e in ca.get('relevant_experience', []):
                    st.markdown(f"- {e}")

                st.markdown("#### 🚀 Key Projects")
                for p in ca.get('projects', []):
                    st.markdown(f"- {p}")

            with col2:
                st.markdown("#### 🔍 Claims Requiring Verification")
                for claim in ca.get('claims_requiring_verification', []):
                    st.warning(f"⚠️ {claim}")

                st.markdown("#### ⚠️ Missing / Weak Areas vs JD")
                for m in ca.get('missing_skills', []):
                    st.error(f"❌ {m}")

# ---------------------------------------------------------
# PAGE 4: JOB FIT MATRIX
# ---------------------------------------------------------
elif page == "🎯 Job Fit Matrix":
    st.markdown('<div class="main-title">Deterministic Job Fit Matrix</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Explainable compatibility calculation comparing Candidate Resume against Job Description.</div>', unsafe_allow_html=True)

    if not st.session_state.active_jd_id or not st.session_state.active_resume_id:
        st.warning("Please select or upload both a Job Description and Candidate Resume first in the sidebar / tabs.")
    else:
        jd_data = db.get_jd(st.session_state.active_jd_id)
        res_data = db.get_resume(st.session_state.active_resume_id)

        if st.button("Calculate Job Fit Matrix"):
            with st.spinner("Calculating explainable fit score..."):
                fit_res = JobFitAnalyzer.calculate_fit(jd_data['role_analysis'], res_data['candidate_analysis'])
                db.save_job_fit(st.session_state.active_jd_id, st.session_state.active_resume_id, fit_res['fit_score'], fit_res)
                st.success("Job Fit calculated & saved!")

        fit_data = db.get_latest_job_fit(st.session_state.active_jd_id, st.session_state.active_resume_id)
        if fit_data:
            fd = fit_data['fit_details']
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown("### 🏆 Overall Fit Score")
                score = fd.get('fit_score', 0)
                st.markdown(f"<h1 style='font-size: 4rem; color: #4F46E5;'>{score}%</h1>", unsafe_allow_html=True)
                st.progress(score / 100.0)

            with c2:
                st.markdown("### 📈 Dimension Breakdown")
                dims = fd.get('dimension_scores', {})
                df_dims = pd.DataFrame({
                    "Dimension": [k.replace('_', ' ').title() for k in dims.keys()],
                    "Score": list(dims.values())
                })
                fig = px.bar(df_dims, x="Score", y="Dimension", orientation='h', range_x=[0, 100], color="Score", color_continuous_scale="Viridis")
                fig.update_layout(height=220, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            col_x, col_y, col_z = st.columns(3)
            with col_x:
                st.markdown("#### ✅ Strong Matches")
                for sm in fd.get('strong_matches', []):
                    st.success(f"• {sm}")
            with col_y:
                st.markdown("#### 🟡 Partial Matches")
                for pm in fd.get('partial_matches', []):
                    st.info(f"• {pm}")
            with col_z:
                st.markdown("#### ❌ Missing / Weak Areas")
                for ma in fd.get('missing_weak_areas', []):
                    st.error(f"• {ma}")

            st.markdown("---")
            st.markdown("### 📐 Methodology & Transparency")
            st.info(fd.get('methodology'))

# ---------------------------------------------------------
# PAGE 5: AI VOICE INTERVIEW
# ---------------------------------------------------------
elif page == "🎙️ AI Voice Interview":
    st.markdown('<div class="main-title">Interactive AI Voice Interview</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">3-Level Adaptive Interview Engine: Screening ➡️ Competency ➡️ Deep Dive.</div>', unsafe_allow_html=True)

    if not st.session_state.active_jd_id or not st.session_state.active_resume_id:
        st.error("Please select a Job Description and Candidate Resume from Dashboard before launching an interview.")
    else:
        # Start or load active session
        if not st.session_state.active_session_id:
            if st.button("🚀 Start New Interview Session"):
                sess_id = interview_engine.start_session(st.session_state.active_jd_id, st.session_state.active_resume_id)
                st.session_state.active_session_id = sess_id
                st.rerun()
        else:
            state = interview_engine.get_session_state(st.session_state.active_session_id)
            
            # Level & Progress Indicator
            cur_lvl = state['current_level']
            lvl_names = {1: "Level 1: Screening", 2: "Level 2: Competency", 3: "Level 3: Deep Dive"}
            
            col_s1, col_s2, col_s3 = st.columns([2, 2, 1])
            with col_s1:
                st.markdown(f"<span class='badge-level'>{lvl_names.get(cur_lvl, 'Level 1')}</span>", unsafe_allow_html=True)
            with col_s2:
                status_text = "Interview Completed 🎉" if state['status'] == 'completed' else f"Session #{state['session_id']} Active"
                st.markdown(f"**Status:** {status_text}")
            with col_s3:
                if st.button("Reset / New Session"):
                    st.session_state.active_session_id = None
                    st.rerun()

            st.markdown("---")

            # Check if pending turn exists or prepare next turn
            pending = state['pending_turn']
            if not pending and state['status'] != 'completed':
                pending = interview_engine.prepare_next_turn(state['session_id'])

            if state['status'] == 'completed':
                st.balloons()
                st.success("🎉 You have completed all 3 levels of the AI Interview!")
                st.info("Head over to the 'Performance Report' and 'Preparation Plan' tabs to view your results!")
            elif pending:
                st.markdown(f"### ❓ Question #{pending['question_number']} (Level {pending['level']})")
                st.markdown(f"**Focus:** `{pending.get('question_focus', 'Competency Evaluation')}`")
                
                question_text = pending['question_text']
                st.markdown(f"> ### \"{question_text}\"")

                # Voice TTS Generation
                tts_bytes = voice_engine.generate_tts_bytes(question_text)
                if tts_bytes:
                    st.audio(tts_bytes, format="audio/mp3", autoplay=True)

                st.markdown("---")
                st.markdown("### 🎙️ Candidate Answer Input")

                # Live Web Speech API JS Component for live transcription directly in browser!
                components_html = """
                <div style="background:#1E293B; padding:15px; border-radius:10px; border:1px solid #334155;">
                    <p style="color:#A5B4FC; font-weight:bold; margin-bottom:8px;">Live Voice Input (Browser Web Speech STT):</p>
                    <button id="start-btn" onclick="startDictation()" style="background:#4F46E5; color:white; border:none; padding:8px 16px; border-radius:6px; cursor:pointer; font-weight:bold;">🎙️ Start Speaking</button>
                    <button id="stop-btn" onclick="stopDictation()" style="background:#EF4444; color:white; border:none; padding:8px 16px; border-radius:6px; cursor:pointer; font-weight:bold; margin-left:8px;">🛑 Stop</button>
                    <p id="speech-status" style="color:#9CA3AF; font-size:12px; margin-top:8px;">Status: Ready to listen...</p>
                </div>
                <script>
                    var recognition;
                    function startDictation() {
                        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                            var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                            recognition = new SpeechRecognition();
                            recognition.continuous = true;
                            recognition.interimResults = true;
                            recognition.lang = 'en-US';

                            recognition.onstart = function() {
                                document.getElementById('speech-status').innerText = "Status: 🎙️ Listening to candidate spoken answer...";
                            };

                            recognition.onresult = function(event) {
                                var transcript = '';
                                for (var i = event.resultIndex; i < event.results.length; ++i) {
                                    transcript += event.results[i][0].transcript;
                                }
                                window.parent.postMessage({type: 'streamlit:setComponentValue', value: transcript}, '*');
                            };

                            recognition.onerror = function(event) {
                                document.getElementById('speech-status').innerText = "Status: Speech Recognition error - " + event.error;
                            };

                            recognition.start();
                        } else {
                            document.getElementById('speech-status').innerText = "Status: Web Speech API not supported in browser. Use text box below.";
                        }
                    }
                    function stopDictation() {
                        if (recognition) {
                            recognition.stop();
                            document.getElementById('speech-status').innerText = "Status: Stopped listening.";
                        }
                    }
                </script>
                """
                st.components.v1.html(components_html, height=130)

                # Answer Text Box (Candidates can type or edit voice transcription)
                answer_input = st.text_area("Answer Transcript / Text Response:", height=140, placeholder="Speak into microphone or type your answer here...")

                if st.button("Submit Answer & Next Question ➡️"):
                    if not answer_input.strip():
                        st.warning("Please provide an answer before submitting.")
                    else:
                        with st.spinner("Evaluating response real-time and adjusting interview difficulty..."):
                            eval_res = interview_engine.submit_answer(
                                session_id=state['session_id'],
                                turn_id=pending['id'],
                                answer_text=answer_input
                            )
                            st.toast(f"Answer Evaluated! Turn Score: {eval_res.get('score', 0)}/100")
                            st.rerun()

            # Display Conversation Trajectory
            if state['turns']:
                st.markdown("---")
                st.markdown("### 📜 Interview Transcript & History")
                for t in reversed(state['turns']):
                    if t['answer_text'] is not None:
                        with st.expander(f"Q#{t['question_number']} (Level {t['level']}) - Score: {t['evaluation'].get('score', 'N/A')}/100"):
                            st.markdown(f"**Q:** {t['question_text']}")
                            st.markdown(f"**A:** {t['answer_text']}")
                            st.markdown(f"**Feedback:** {t['evaluation'].get('feedback')}")
                            st.markdown(f"**Strengths:** {', '.join(t['evaluation'].get('strengths', []))}")
                            st.markdown(f"**Areas for Improvement:** {', '.join(t['evaluation'].get('weaknesses', []))}")

# ---------------------------------------------------------
# PAGE 6: PERFORMANCE REPORT
# ---------------------------------------------------------
elif page == "📊 Performance Report":
    st.markdown('<div class="main-title">Interview Performance Report</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Comprehensive multi-dimensional evaluation of interview performance.</div>', unsafe_allow_html=True)

    if not st.session_state.active_session_id:
        st.warning("No active interview session found. Complete an interview session under 'AI Voice Interview' tab.")
    else:
        state = interview_engine.get_session_state(st.session_state.active_session_id)
        
        if st.button("Generate Final Report"):
            with st.spinner("Generating performance analytics..."):
                rep_data = report_gen.generate_report(state)
                db.save_performance_report(state['session_id'], rep_data['overall_score'], rep_data)
                st.success("Performance report generated successfully!")

        report_db = db.get_performance_report(state['session_id'])
        if report_db:
            rep = report_db['report']
            
            st.markdown(f"### 🏆 Candidate Readiness: **{rep.get('interview_readiness', 'Evaluated')}**")
            st.info(rep.get('executive_summary'))

            # Metric Cards
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Overall Score", f"{rep.get('overall_score')}%")
            c2.metric("Role Fit", f"{rep.get('role_fit')}%")
            c3.metric("Technical Knowledge", f"{rep.get('technical_knowledge')}%")
            c4.metric("Problem Solving", f"{rep.get('problem_solving')}%")

            c5, c6, c7, c8 = st.columns(4)
            c5.metric("Communication", f"{rep.get('communication')}%")
            c6.metric("Confidence", f"{rep.get('confidence')}%")
            c7.metric("Depth of Understanding", f"{rep.get('depth_of_understanding')}%")
            c8.metric("Behavioural Fit", f"{rep.get('behavioural_fit')}%")

            st.markdown("---")
            # Radar Chart Visualization
            st.markdown("### 🕸️ Competency Radar Chart")
            categories = ['Technical Knowledge', 'Problem Solving', 'Communication', 'Confidence', 'Depth of Understanding', 'Behavioural Fit', 'Role Fit']
            values = [
                rep.get('technical_knowledge', 70),
                rep.get('problem_solving', 70),
                rep.get('communication', 70),
                rep.get('confidence', 70),
                rep.get('depth_of_understanding', 70),
                rep.get('behavioural_fit', 70),
                rep.get('role_fit', 70)
            ]

            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill='toself',
                name='Candidate Rating',
                line_color='#4F46E5'
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=False,
                height=380
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 💪 Key Strengths")
                for s in rep.get('strengths', []):
                    st.success(f"• {s}")
            with col2:
                st.markdown("#### ⚠️ Weaknesses & Preparation Gaps")
                for w in rep.get('weaknesses', []):
                    st.error(f"• {w}")

            st.markdown("---")
            st.markdown("### 📝 Question-by-Question Granular Feedback")
            for qf in rep.get('question_feedback', []):
                with st.expander(f"Question #{qf.get('question_number')} (Level {qf.get('level')}) - Score: {qf.get('score')}/100"):
                    st.markdown(f"**Question:** {qf.get('question')}")
                    st.markdown(f"**Candidate Response:** {qf.get('candidate_answer')}")
                    st.markdown(f"**Feedback:** {qf.get('feedback')}")
                    st.markdown(f"**Key Takeaway:** {qf.get('key_takeaway')}")

# ---------------------------------------------------------
# PAGE 7: PREPARATION PLAN
# ---------------------------------------------------------
elif page == "📚 Preparation Plan":
    st.markdown('<div class="main-title">Personalized Preparation Plan</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Prioritized study topics, concrete learning resources, drills, and STAR strategy.</div>', unsafe_allow_html=True)

    if not st.session_state.active_session_id:
        st.warning("No active interview session found. Complete an interview session to generate a preparation plan.")
    else:
        state = interview_engine.get_session_state(st.session_state.active_session_id)
        report_db = db.get_performance_report(state['session_id'])

        if not report_db:
            st.info("Please generate your Performance Report under 'Performance Report' tab first.")
        else:
            if st.button("Generate Preparation Plan"):
                with st.spinner("Formulating personalized study curriculum..."):
                    plan_data = prep_planner.generate_plan(
                        report_data=report_db['report'],
                        role_analysis=state['jd']['role_analysis'],
                        candidate_analysis=state['resume']['candidate_analysis']
                    )
                    db.save_preparation_plan(state['session_id'], plan_data)
                    st.success("Preparation Plan generated!")

            plan_db = db.get_preparation_plan(state['session_id'])
            if plan_db:
                plan = plan_db['plan']
                st.markdown(f"### 🎯 {plan.get('title')}")
                st.info(plan.get('summary'))

                st.markdown("---")
                st.markdown("### 🔝 Prioritized Focus Topics")
                for top in plan.get('prioritized_topics', []):
                    prio_color = "🔴" if top.get('priority') == "High" else ("🟡" if top.get('priority') == "Medium" else "🟢")
                    st.markdown(f"#### {prio_color} Priority: {top.get('topic')}")
                    st.markdown(f"**Why Important:** {top.get('why_important')}")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**Concrete Study Items:**")
                        for item in top.get('concrete_study_items', []):
                            st.markdown(f"- {item}")
                    with c2:
                        st.markdown("**Recommended Resources:**")
                        for res in top.get('recommended_resources', []):
                            st.markdown(f"- 📖 {res}")
                    st.markdown("---")

                st.markdown("### 🛠️ Actionable Projects & Practical Drills")
                for proj in plan.get('actionable_projects_or_drills', []):
                    st.markdown(f"• {proj}")

                st.markdown("---")
                st.markdown("### 🗣️ STAR Method Response Strategy")
                for star in plan.get('behavioural_star_strategy', []):
                    st.markdown(f"⭐ {star}")

                st.markdown("---")
                st.markdown("### ❓ Recommended Practice Mock Questions")
                for mq in plan.get('recommended_mock_questions', []):
                    st.markdown(f"❓ *\"{mq}\"*")
