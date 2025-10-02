from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "ok"
    assert "time" in body

def test_detect_contract():
    r = client.post("/api/v1/detect", json={"text": "Troponin was checked."})
    assert r.status_code == 200
    spans = r.json().get("spans")
    assert isinstance(spans, list)
    assert spans and "canonical" in spans[0] and "category" in spans[0]

def test_simplify_contract():
    r = client.post("/api/v1/simplify", json={"text": "Patient presents with chest pain."})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data.get("text"), str)
    assert isinstance(data.get("grade"), (int, float))

def test_spellcheck_contract():
    r = client.post("/api/v1/spellcheck", json={"text": "helo"})
    assert r.status_code == 200
    assert isinstance(r.json().get("text"), str)

def test_classify_contract():
    r = client.post("/api/v1/classify", json={"sentences": ["a", "b", "c"]})
    assert r.status_code == 200
    labels = r.json().get("labels")
    assert isinstance(labels, list) and len(labels) == 3
