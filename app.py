import streamlit as st
import os
import tempfile
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from agent.jd_parser import parse_jd
from agent.resume_parser import parse_resume
from agent.scorer import score_candidate
from agent.ranker import rank_candidates
from agent.override import apply_override

st.set_page_config(page_title="RecruitAgent", page_icon="🤖", layout="wide")

st.title("🤖 RecruitAgent")
st.caption("AI-powered HR Resume Shortlisting Agent")

# Session state init
if "ranked_candidates" not in st.session_state:
    st.session_state.ranked_candidates = []
if "parsed_jd" not in st.session_state:
    st.session_state.parsed_jd = None
if "report_html" not in st.session_state:
    st.session_state.report_html = None

# SIDEBAR
with st.sidebar:
    st.header("📋 Instructions")
    st.markdown("""
    1. Enter or paste the Job Description
    2. Upload candidate resumes (PDF or DOCX)
    3. Click **Analyse Candidates**
    4. Review the ranked shortlist
    5. Apply overrides if needed
    6. Download the final report
    """)
    st.divider()
    st.caption("RecruitAgent v1.0 | Rizul Gupta")

# STEP 1 - JD INPUT
st.header("Step 1 — Job Description")
jd_text = st.text_area(
    "Paste the Job Description here",
    height=200,
    placeholder="Enter the full job description including required skills, experience, and responsibilities..."
)

# STEP 2 - RESUME UPLOAD
st.header("Step 2 — Upload Resumes")
uploaded_files = st.file_uploader(
    "Upload candidate resumes (PDF or DOCX)",
    type=["pdf", "docx"],
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"{len(uploaded_files)} resume(s) uploaded successfully")

# STEP 3 - ANALYSE
st.header("Step 3 — Analyse")
if st.button("🚀 Analyse Candidates", type="primary"):
    if not jd_text.strip():
        st.error("Please enter a Job Description first")
    elif not uploaded_files:
        st.error("Please upload at least one resume")
    else:
        with st.spinner("Parsing Job Description..."):
            try:
                parsed_jd = parse_jd(jd_text)
                st.session_state.parsed_jd = parsed_jd
                st.success("✅ Job Description parsed")
            except Exception as e:
                st.error(f"Failed to parse JD: {e}")
                st.stop()

        scores = []
        for uploaded_file in uploaded_files:
            with st.spinner(f"Processing {uploaded_file.name}..."):
                try:
                    # Save to temp file
                    suffix = ".pdf" if uploaded_file.name.endswith(".pdf") else ".docx"
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(uploaded_file.read())
                        tmp_path = tmp.name

                    resume = parse_resume(tmp_path)
                    score = score_candidate(parsed_jd, resume)
                    scores.append(score)
                    st.success(f"✅ {resume.candidate_name} scored: {score.total_score}/10")
                    os.unlink(tmp_path)

                except Exception as e:
                    st.warning(f"⚠️ Could not process {uploaded_file.name}: {e}")

        if scores:
            st.session_state.ranked_candidates = rank_candidates(scores)
            st.success(f"✅ All candidates ranked. Top candidate: {st.session_state.ranked_candidates[0].candidate_name}")

# STEP 4 - RESULTS
if st.session_state.ranked_candidates:
    st.header("Step 4 — Ranked Shortlist")

    for i, candidate in enumerate(st.session_state.ranked_candidates):
        color = "🟢" if candidate.recommendation == "HIRE" else "🔴"
        with st.expander(f"{color} #{i+1} {candidate.candidate_name} — {candidate.total_score}/10 — {candidate.recommendation}"):
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.metric("Skills Match", f"{candidate.skills_match.score}/10")
                st.caption(candidate.skills_match.justification)
            with col2:
                st.metric("Experience", f"{candidate.experience_relevance.score}/10")
                st.caption(candidate.experience_relevance.justification)
            with col3:
                st.metric("Education", f"{candidate.education_and_certs.score}/10")
                st.caption(candidate.education_and_certs.justification)
            with col4:
                st.metric("Projects", f"{candidate.project_portfolio.score}/10")
                st.caption(candidate.project_portfolio.justification)
            with col5:
                st.metric("Communication", f"{candidate.communication_quality.score}/10")
                st.caption(candidate.communication_quality.justification)

    # STEP 5 - OVERRIDE
    st.header("Step 5 — Human Override")
    st.caption("Adjust any candidate score with a documented reason")

    candidate_names = [c.candidate_name for c in st.session_state.ranked_candidates]
    selected_name = st.selectbox("Select Candidate", candidate_names)
    selected_dimension = st.selectbox("Select Dimension", [
        "skills_match", "experience_relevance",
        "education_and_certs", "project_portfolio", "communication_quality"
    ])
    new_score = st.slider("New Score", 0.0, 10.0, 5.0, 0.5)
    override_reason = st.text_input("Reason for Override (mandatory)")

    if st.button("Apply Override"):
        if not override_reason.strip():
            st.error("Please provide a reason for the override")
        else:
            idx = candidate_names.index(selected_name)
            st.session_state.ranked_candidates[idx] = apply_override(
                st.session_state.ranked_candidates[idx],
                selected_dimension,
                new_score,
                override_reason
            )
            st.session_state.ranked_candidates = rank_candidates(st.session_state.ranked_candidates)
            st.success(f"Override applied and rankings updated")
            st.rerun()

    # STEP 6 - REPORT
    st.header("Step 6 — Download Report")

    if st.button("📄 Generate Report"):
        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template("report.html")

        hire_count = sum(1 for c in st.session_state.ranked_candidates if c.recommendation == "HIRE")
        report_html = template.render(
            generated_at=datetime.now().strftime("%d %b %Y, %I:%M %p"),
            job_role="See Job Description",
            total_candidates=len(st.session_state.ranked_candidates),
            hire_count=hire_count,
            no_hire_count=len(st.session_state.ranked_candidates) - hire_count,
            top_score=st.session_state.ranked_candidates[0].total_score,
            candidates=st.session_state.ranked_candidates
        )
        st.session_state.report_html = report_html
        st.success("Report generated successfully")

    if st.session_state.report_html:
        st.download_button(
            label="⬇️ Download HTML Report",
            data=st.session_state.report_html,
            file_name=f"shortlist_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            mime="text/html"
        )