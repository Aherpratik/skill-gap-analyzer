# src/film_gap/api/main.py
from fastapi import FastAPI, Form
from pydantic import BaseModel
from pathlib import Path
from typing import List, Set


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

def compute_fit(resume_skills: Set[str], jd_required: Set[str]) -> ScoreOut:
    matched = sorted(resume_skills & jd_required)
    missing = sorted(jd_required - resume_skills)
    coverage = len(matched) / max(1, len(jd_required))
    # simple v1 score = coverage only (0..1). You can extend later.
    return ScoreOut(fit_score=round(coverage, 3),
                    matched_required=matched,
                    missing_required=missing)

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
    r_skills = set(extract_skills(resume_text, TAXO))
    j_skills = set(extract_skills(jd_text, TAXO))  # treat all as required in v1
    return compute_fit(r_skills, j_skills)
