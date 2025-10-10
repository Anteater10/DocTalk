from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_simplify_rules_and_grade():
    text = "Findings indicate elevated troponin. Recommend echo; patient denies chest pain."
    spans = [{
        "start": 27, "end": 34, "surface": "troponin",
        "canonical": "troponin", "category": "test", "negated": False,
        "definition": "a blood test for heart damage", "why": "Elevated suggests heart injury"
    },{
        "start": 49, "end": 52, "surface": "echo",
        "canonical": "echocardiogram", "category": "test", "negated": False,
        "definition": "ultrasound of the heart", "why": "Shows heart structure and function"
    }]
    r = client.post("/api/v1/simplify", json={"text": text, "spans": spans})
    assert r.status_code == 200
    data = r.json()
    assert "troponin (a blood test for heart damage)" in data["text"].lower()
    assert "we suggest" in data["text"].lower()
    assert data["grade"] <= 8.5
    assert data["diagnostics"]["sentences"] >= 2.0
