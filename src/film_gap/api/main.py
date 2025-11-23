# src/film_gap/api/main.py

from __future__ import annotations

from pathlib import Path
from typing import List, Set
import math

from fastapi import FastAPI, Form, UploadFile, File
from pydantic import BaseModel

from film_gap.nlp.extract import load_taxonomy, extract_skills, guess_years, predict_role
from film_gap.nlp.embeddings import embed_text, cosine_similarity
from film_gap.utils.file_reader import extract_text_from_upload


app = FastAPI(title="Skill Gap Analyzer", version="0.3.0")

# ---------------------------
# Load taxonomy
# ---------------------------
TAXO_CSV = Path(__file__).resolve().parents[1] / "nlp" / "taxonomy" / "skills.csv"
TAXO = load_taxonomy(TAXO_CSV)


# ---------------------------
# Models
# ---------------------------
class ExtractOut(BaseModel):
    skills: List[str]
    role: str
    years: int


class ScoreOut(BaseModel):
    fit_score: float
    matched_required: List[str]
    missing_required: List[str]
    role_match: bool
    years_candidate: int
    years_required: int


class SemanticScoreOut(BaseModel):
    semantic_score: float
    matched_required: List[str]
    missing_required: List[str]


# ---------------------------
# Helper: rule-based fit
# ---------------------------
def compute_fit(
    resume_skills: Set[str],
    jd_required: Set[str],
    role_match: bool,
    years_candidate: int,
    years_required: int,
) -> ScoreOut:

    matched = sorted(resume_skills & jd_required)
    missing = sorted(jd_required - resume_skills)

    coverage = len(matched) / max(1, len(jd_required))

    delta_years = years_candidate - years_required
    exp_term = 1 / (1 + math.exp(-delta_years / 2.0)) if years_required > 0 else 0.5

    role_term = 1.0 if role_match else 0.0

    fit = 0.6 * coverage + 0.25 * exp_term + 0.15 * role_term

    return ScoreOut(
        fit_score=round(fit, 3),
        matched_required=matched,
        missing_required=missing,
        role_match=role_match,
        years_candidate=years_candidate,
        years_required=years_required,
    )


# ---------------------------
# Health
# ---------------------------
@app.get("/healthz")
def health():
    return {"ok": True}


# ---------------------------
# Extraction endpoints
# ---------------------------
@app.post("/extract/resume", response_model=ExtractOut)
def extract_resume(text: str = Form(...)):
    return ExtractOut(
        skills=extract_skills(text, TAXO),
        role=predict_role(text),
        years=guess_years(text),
    )


@app.post("/extract/jd", response_model=ExtractOut)
def extract_jd(text: str = Form(...)):
    return ExtractOut(
        skills=extract_skills(text, TAXO),
        role=predict_role(text),
        years=guess_years(text),
    )


# ---------------------------
# Rule-based score
# ---------------------------
@app.post("/score/pair", response_model=ScoreOut)
def score_pair(resume_text: str = Form(...), jd_text: str = Form(...)):
    resume_skills = set(extract_skills(resume_text, TAXO))
    jd_skills = set(extract_skills(jd_text, TAXO))

    role_resume = predict_role(resume_text)
    role_jd = predict_role(jd_text)
    role_match = role_resume != "UNKNOWN" and role_resume == role_jd

    return compute_fit(
        resume_skills,
        jd_skills,
        role_match,
        guess_years(resume_text),
        guess_years(jd_text),
    )


# ---------------------------
# Semantic score (TEXT → MiniLM)
# ---------------------------
@app.post("/score/semantic", response_model=SemanticScoreOut)
def score_semantic(resume_text: str = Form(...), jd_text: str = Form(...)):

    vec_r = embed_text(resume_text)
    vec_j = embed_text(jd_text)

    sim = cosine_similarity(vec_r, vec_j)  # -1..1
    sim_norm = max(0.0, min(1.0, (sim + 1) / 2.0))  # → 0..1

    resume_skills = set(extract_skills(resume_text, TAXO))
    jd_skills = set(extract_skills(jd_text, TAXO))

    return SemanticScoreOut(
        semantic_score=round(sim_norm, 3),
        matched_required=sorted(resume_skills & jd_skills),
        missing_required=sorted(jd_skills - resume_skills),
    )


# ---------------------------
# Semantic score (FILE upload → text → MiniLM)
# ---------------------------
@app.post("/score/semantic/file", response_model=SemanticScoreOut)
async def score_semantic_file(
    resume_file: UploadFile = File(...),
    jd_file: UploadFile = File(...),
):
    # 1) extract text from files
    resume_text = extract_text_from_upload(resume_file)
    jd_text = extract_text_from_upload(jd_file)

    # 2) embeddings
    vec_r = embed_text(resume_text)
    vec_j = embed_text(jd_text)

    sim = cosine_similarity(vec_r, vec_j)
    sim_norm = max(0.0, min(1.0, (sim + 1) / 2.0))

    # 3) taxonomy skills for explainability
    resume_skills = set(extract_skills(resume_text, TAXO))
    jd_skills = set(extract_skills(jd_text, TAXO))

    return SemanticScoreOut(
        semantic_score=round(sim_norm, 3),
        matched_required=sorted(resume_skills & jd_skills),
        missing_required=sorted(jd_skills - resume_skills),
    )
