# src/film_gap/api/main.py
from fastapi import FastAPI, Form
from pydantic import BaseModel
from pathlib import Path
from typing import List, Set
import math

from film_gap.nlp.extract import load_taxonomy, extract_skills, guess_years, predict_role

app = FastAPI(title="Skill Gap Analyzer", version="0.0.2")

# Resolve to src/film_gap/nlp/taxonomy/skills.csv
TAXO_CSV = Path(__file__).resolve().parents[1] / "nlp" / "taxonomy" / "skills.csv"
TAXO = load_taxonomy(TAXO_CSV)


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


def compute_fit(
    resume_skills: Set[str],
    jd_required: Set[str],
    role_match: bool,
    years_candidate: int,
    years_required: int,
) -> ScoreOut:
    matched = sorted(resume_skills & jd_required)
    missing = sorted(jd_required - resume_skills)

    coverage = len(matched) / max(1, len(jd_required))  # 0..1

    # experience term: logistic around (candidate - required)
    delta_years = years_candidate - years_required
    exp_term = 1 / (1 + math.exp(-delta_years / 2)) if years_required > 0 else 0.5

    role_term = 1.0 if role_match else 0.0

    # weighted sum
    fit = (
        0.6 * coverage +  # skills are most important
        0.25 * exp_term +
        0.15 * role_term
    )

    return ScoreOut(
        fit_score=round(fit, 3),
        matched_required=matched,
        missing_required=missing,
        role_match=role_match,
        years_candidate=years_candidate,
        years_required=years_required,
    )

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/extract/resume", response_model=ExtractOut)
def extract_resume(text: str = Form(...)):
    skills = extract_skills(text, TAXO)
    role = predict_role(text)
    years = guess_years(text)
    return ExtractOut(skills=skills, role=role, years=years)

@app.post("/extract/jd")
def extract_jd(text: str = Form(...)):
    skills = extract_skills(text, TAXO)
    # simple v1: treat all detected skills as "required"
    return {"skills": skills}

@app.post("/score/pair", response_model=ScoreOut)
def score_pair(resume_text: str = Form(...), jd_text: str = Form(...)):
    resume_skills = set(extract_skills(resume_text, TAXO))
    jd_skills = set(extract_skills(jd_text, TAXO))

    # heuristics for now – later we can parse from JD separately
    years_candidate = guess_years(resume_text)
    years_required = guess_years(jd_text)

    role_resume = predict_role(resume_text)
    role_jd = predict_role(jd_text)
    role_match = role_resume != "UNKNOWN" and role_resume == role_jd

    return compute_fit(
        resume_skills=resume_skills,
        jd_required=jd_skills,
        role_match=role_match,
        years_candidate=years_candidate,
        years_required=years_required,
    )

