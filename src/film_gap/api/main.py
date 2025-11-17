from fastapi import FastAPI

app = FastAPI(title="Skill Gap Analyzer", version="0.0.1")

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/ping")
def ping():
    return {"pong": True}
