# app.py

import streamlit as st
import requests
BASE = "http://127.0.0.1:8000"




st.set_page_config(page_title="Skill Gap Analyzer", layout="wide")
st.title("🎬 Skill Gap Analyzer")

st.sidebar.header("Backend Status")
st.sidebar.write("FastAPI running at:")
st.sidebar.code(BASE)

# =========================================================
# TEXT MODE
# =========================================================

st.header("✏️ Text Input Mode")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Resume (Text)")
    resume_text = st.text_area("Paste Resume Text", height=200)

    if st.button("Extract Resume Skills (Text)"):
        if not resume_text.strip():
            st.warning("Paste resume text first.")
        else:
            resp = requests.post(f"{BASE}/extract/resume", data={"text": resume_text})
            st.write(resp.json())

with col2:
    st.subheader("Job Description (Text)")
    jd_text = st.text_area("Paste JD Text", height=200)

    if st.button("Extract JD Skills (Text)"):
        if not jd_text.strip():
            st.warning("Paste JD text first.")
        else:
            resp = requests.post(f"{BASE}/extract/jd", data={"text": jd_text})
            st.write(resp.json())

st.subheader("⚖️ Compare Resume vs JD (Rule-Based Scoring)")
if st.button("Compute Fit Score (Text Mode)"):
    if not resume_text.strip() or not jd_text.strip():
        st.warning("Paste BOTH resume and JD text.")
    else:
        resp = requests.post(
            f"{BASE}/score/pair",
            data={"resume_text": resume_text, "jd_text": jd_text},
        )
        out = resp.json()
        st.metric("Rule-Based Fit Score", f"{out['fit_score']*100:.1f} %")
        st.write(out)

st.subheader("🧠 Semantic Similarity (Text)")
if st.button("Compute Semantic Match (Text Mode)"):
    if not resume_text.strip() or not jd_text.strip():
        st.warning("Paste BOTH resume and JD text.")
    else:
        resp = requests.post(
            f"{BASE}/score/semantic",
            data={"resume_text": resume_text, "jd_text": jd_text},
        )
        if resp.status_code != 200:
            st.error(f"Backend error {resp.status_code}")
            st.code(resp.text)
        else:
            out = resp.json()
            st.metric("Semantic Match Score (Text)", f"{out['semantic_score']*100:.1f} %")
            st.write(out)

st.markdown("---")

# =========================================================
# FILE MODE
# =========================================================

st.header("📁 Upload Files (PDF / DOCX / TXT)")

col3, col4 = st.columns(2)

with col3:
    st.subheader("Resume File")
    resume_file = st.file_uploader(
        "Upload Resume (PDF, DOCX, TXT)",
        type=["pdf", "docx", "txt"],
        key="resume_file",
    )

with col4:
    st.subheader("Job Description File")
    jd_file = st.file_uploader(
        "Upload JD (PDF, DOCX, TXT)",
        type=["pdf", "docx", "txt"],
        key="jd_file",
    )

if st.button("Compute Semantic Match (Files Mode)"):
    if not resume_file or not jd_file:
        st.warning("Upload BOTH Resume + JD files.")
    else:
        files = {
            "resume_file": (
                resume_file.name,
                resume_file.getvalue(),
                resume_file.type or "application/octet-stream",
            ),
            "jd_file": (
                jd_file.name,
                jd_file.getvalue(),
                jd_file.type or "application/octet-stream",
            ),
        }

        resp = requests.post(f"{BASE}/score/semantic/file", files=files)

        if resp.status_code != 200:
            st.error(f"Backend error {resp.status_code}")
            st.code(resp.text)
        else:
            out = resp.json()
            # debug: show raw response
            st.write("Raw backend response:", out)

            if "semantic_score" not in out:
                st.error("Key 'semantic_score' missing in backend response.")
            else:
                st.metric(
                    "Semantic Match Score (Files)",
                    f"{out['semantic_score']*100:.1f} %",
                )
                st.write(out)
