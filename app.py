import streamlit as st
import requests

st.set_page_config(page_title="Film Industry Skill Gap Analyzer", layout="wide")
st.title("🎬 Skill Gap Analyzer")

BASE_URL = "http://127.0.0.1:8000"

st.sidebar.header("Backend")
st.sidebar.write("Make sure your FastAPI server is running at:")
st.sidebar.code(BASE_URL)

col1, col2 = st.columns(2)

with col1:
    st.subheader("🎭 Resume")
    resume_text = st.text_area("Paste Resume Text", height=250)
    if st.button("Extract Resume Skills"):
        res = requests.post(f"{BASE_URL}/extract/resume", data={"text": resume_text})
        st.json(res.json())

with col2:
    st.subheader("🎬 Job Description (JD)")
    jd_text = st.text_area("Paste JD Text", height=250)
    if st.button("Extract JD Skills"):
        res = requests.post(f"{BASE_URL}/extract/jd", data={"text": jd_text})
        st.json(res.json())

st.markdown("---")
st.header("⚖️ Compare Resume vs JD")

if st.button("Compute Fit Score"):
    if not resume_text or not jd_text:
        st.warning("Please enter both Resume AND JD text.")
    else:
        payload = {"resume_text": resume_text, "jd_text": jd_text}
        res = requests.post(f"{BASE_URL}/score/pair", data=payload)
        result = res.json()

        st.subheader("Fit Score")
        st.metric(label="Compatibility", value=f"{result['fit_score']*100:.1f}%")

        st.subheader("Matched Skills (backend sees)")
        st.text(", ".join(result["matched_required"]))

        st.subheader("Missing Skills (backend expects)")
        missing = result["missing_required"]
        st.text(", ".join(missing) if missing else "None 🎉 Full match!")
