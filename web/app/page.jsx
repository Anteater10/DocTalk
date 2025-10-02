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
  const [text, setText] = useState(
    "Sample note: blood pressure was recorded. Troponin was checked in the ER."
  );
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
      if (!res.ok) {
        throw new Error(`API error ${res.status}`);
      }
      const data = await res.json();
      setSpans(Array.isArray(data.spans) ? data.spans : []);
    } catch (e) {
      console.error(e);
      setError("Could not explain the text. Is the API running on :8000?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ padding: 24, fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, Arial" }}>
      <h1 style={{ marginBottom: 8 }}>DocTalk</h1>
      <p style={{ margin: 0, opacity: 0.8 }}>Sprint 1: Paste → Explain → Highlights</p>

      <section style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 16 }}>
        {/* Left: input */}
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <label htmlFor="note" style={{ fontWeight: 600 }}>Paste clinical text</label>
          <textarea
            id="note"
            rows={10}
            value={text}
            onChange={(e) => setText(e.target.value)}
            style={{
              width: "100%",
              resize: "vertical",
              padding: 12,
              border: "1px solid #333",
              borderRadius: 8,
              background: "#111",
              color: "white",
            }}
          />
          <div style={{ display: "flex", gap: 8 }}>
            <button
              onClick={onExplain}
              disabled={loading || !text.trim()}
              style={{
                padding: "10px 14px",
                borderRadius: 8,
                border: "1px solid #444",
                background: loading ? "#333" : "#1f6feb",
                color: "white",
                cursor: loading ? "not-allowed" : "pointer",
                fontWeight: 600,
              }}
            >
              {loading ? "Explaining…" : "Explain"}
            </button>
            <small style={{ opacity: 0.7 }}>
              Tip: Include the word “troponin” to see a different highlight from the stub.
            </small>
          </div>
          {error && (
            <div style={{ marginTop: 8, color: "#ff6b6b" }}>
              {error}
            </div>
          )}
        </div>

        {/* Right: output */}
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <strong>Highlights</strong>
          <div
            style={{
              minHeight: 160,
              padding: 12,
              border: "1px solid #333",
              borderRadius: 8,
              background: "#0b0b0b",
              color: "white",
              lineHeight: 1.6,
            }}
          >
            {renderHighlighted(text, spans)}
          </div>

          {/* Legend */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 8 }}>
            {Object.entries(CATEGORY_COLORS).map(([cat, color]) => (
              <span key={cat} style={{ display: "inline-flex", gap: 8, alignItems: "center" }}>
                <span
                  style={{
                    display: "inline-block",
                    width: 12,
                    height: 12,
                    borderRadius: 4,
                    background: color,
                    border: "1px solid #222",
                  }}
                />
                <small style={{ opacity: 0.8 }}>{cat}</small>
              </span>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}

/** Render text with non-overlapping highlighted spans (0-based, inclusive end). */
function renderHighlighted(text, spans) {
  if (!text) return null;
  if (!Array.isArray(spans) || spans.length === 0) return <span>{text}</span>;

  // sort by start asc, longer spans first in case of ties
  const sorted = [...spans].sort((a, b) => a.start - b.start || (b.end - b.start) - (a.end - a.start));
  const pieces = [];
  let cursor = 0;

  for (let i = 0; i < sorted.length; i++) {
    const s = sorted[i];
    const start = Math.max(0, s.start);
    const end = Math.min(text.length - 1, s.end); // inclusive

    if (Number.isNaN(start) || Number.isNaN(end) || start > end || start >= text.length) {
      continue; // skip bad spans safely
    }

    // gap before highlight
    if (cursor < start) {
      pieces.push(<span key={`g-${cursor}-${start}`}>{text.slice(cursor, start)}</span>);
    }

    const surf = text.slice(start, end + 1);
    const bg = CATEGORY_COLORS[s.category] || "#444";

    pieces.push(
      <mark
        key={`m-${start}-${end}`}
        style={{
          background: bg,
          color: "black",
          padding: "0 2px",
          borderRadius: 4,
        }}
        title={tooltipFromSpan(s)}
      >
        {surf}
      </mark>
    );

    cursor = end + 1;
  }

  // tail after last highlight
  if (cursor < text.length) {
    pieces.push(<span key={`t-${cursor}`}>{text.slice(cursor)}</span>);
  }

  return pieces;
}

function tooltipFromSpan(s) {
  const bits = [];
  if (s.canonical) bits.push(s.canonical);
  if (s.category) bits.push(`(${s.category})`);
  if (s.negated) bits.push("[not present]");
  if (s.definition) bits.push(`— ${s.definition}`);
  return bits.join(" ");
}
