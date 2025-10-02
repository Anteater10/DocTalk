"use client";

import { useState } from "react";

const CATEGORY_COLORS = {
  diagnosis: "#ffd166",
  procedure: "#a0c4ff",
  medication: "#bdb2ff",
  test: "#9bf6ff",
  anatomy: "#caffbf",
  measurement: "#ffadad",
};

export default function Page() {
  const [text, setText] = useState("Sample note: blood pressure was recorded. Troponin was checked.");
  const [spans, setSpans] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function onExplain() {
    setLoading(true);
    setError("");
    setSpans([]);
    try {
      const res = await fetch("http://localhost:8000/api/v1/detect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) throw new Error(`API error ${res.status}`);
      const data = await res.json();
      setSpans(Array.isArray(data.spans) ? data.spans : []);
    } catch {
      setError("Could not reach API");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ padding: 24 }}>
      <h1>DocTalk</h1>
      <textarea rows={6} value={text} onChange={e => setText(e.target.value)} style={{ width: "100%" }} />
      <div>
        <button onClick={onExplain} disabled={loading}>{loading ? "Explaining…" : "Explain"}</button>
      </div>
      {error && <div style={{ color: "red" }}>{error}</div>}
      <div style={{ marginTop: 16, padding: 12, border: "1px solid #444" }}>
        {renderHighlighted(text, spans)}
      </div>
    </main>
  );
}

function renderHighlighted(text, spans) {
  if (!spans?.length) return <span>{text}</span>;
  const parts = [];
  let pos = 0;
  spans.forEach((s, i) => {
    if (pos < s.start) parts.push(<span key={`g-${i}`}>{text.slice(pos, s.start)}</span>);
    parts.push(
      <mark key={`m-${i}`} style={{ background: CATEGORY_COLORS[s.category] || "#ccc" }}>
        {text.slice(s.start, s.end + 1)}
      </mark>
    );
    pos = s.end + 1;
  });
  if (pos < text.length) parts.push(<span key="end">{text.slice(pos)}</span>);
  return parts;
}
