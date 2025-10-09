# DocTalk/api/app/db/repo.py
# DocTalk/api/app/db/repo.py

from __future__ import annotations
from pathlib import Path
import csv

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from .models import Base, Term, Alias, Acronym, Unit

# DB engine (reads DATABASE_URL from .env)
engine = create_engine(settings.DATABASE_URL, future=True)

SCHEMA_PATH = Path(__file__).with_name("schema.sql")
DATA_DIR = Path(__file__).parents[1] / "data"

def init_db() -> None:
    """Apply schema.sql and create ORM tables."""
    with engine.begin() as conn:
        if SCHEMA_PATH.exists():
            conn.execute(text(SCHEMA_PATH.read_text()))
    Base.metadata.create_all(engine)

def seed() -> None:
    """Load CSV seeds into Postgres."""
    terms_csv = DATA_DIR / "glossary_seed.csv"
    acr_csv = DATA_DIR / "acronyms_seed.csv"
    units_csv = DATA_DIR / "units_seed.csv"

    with Session(engine) as s:
        # ---- Terms ----
        if terms_csv.exists():
            with terms_csv.open(newline="", encoding="utf-8-sig") as f:
                r = csv.DictReader(f)
                for row in r:
                    canonical = (row.get("canonical") or "").strip()
                    category = (row.get("category") or "").strip()
                    if not canonical or not category:
                        continue  # skip incomplete rows
                    definition = ((row.get("definition") or "").strip() or None)
                    why = ((row.get("why") or "").strip() or None)
                    alias_val = ((row.get("alias") or "").strip() or None)

                    term = s.scalar(select(Term).where(Term.canonical == canonical))
                    if not term:
                        term = Term(
                            canonical=canonical,
                            category=category,
                            definition=definition,
                            why=why,
                        )
                        s.add(term)
                        s.flush()

                    if alias_val:
                        exists = s.scalar(select(Alias).where(Alias.alias == alias_val))
                        if not exists:
                            s.add(Alias(term_id=term.id, alias=alias_val))

        # ---- Acronyms ----
        if acr_csv.exists():
            with acr_csv.open(newline="", encoding="utf-8-sig") as f:
                r = csv.DictReader(f)
                for row in r:
                    ac = (row.get("acronym") or "").strip()
                    if not ac:
                        continue
                    expansions = [x.strip() for x in (row.get("expansions") or "").split("|") if x.strip()]
                    clues = [seg.strip().split("/") for seg in (row.get("clues") or "").split("|") if seg.strip()]
                    if not expansions:
                        continue
                    exists = s.scalar(select(Acronym).where(Acronym.acronym == ac))
                    if not exists:
                        s.add(Acronym(acronym=ac, expansions=expansions, clues=clues))

        # ---- Units ----
        if units_csv.exists():
            with units_csv.open(newline="", encoding="utf-8-sig") as f:
                r = csv.DictReader(f)
                for row in r:
                    u = (row.get("unit") or "").strip()
                    canonical_u = (row.get("canonical") or "").strip()
                    kind = (row.get("kind") or "").strip()
                    if not u or not canonical_u or not kind:
                        continue
                    exists = s.scalar(select(Unit).where(Unit.unit == u))
                    if not exists:
                        s.add(Unit(unit=u, canonical=canonical_u, kind=kind))

        s.commit()

def alias_to_term_map() -> dict[str, dict]:
    """Return { alias_lower: {canonical, category, definition, why} }"""
    out: dict[str, dict] = {}
    with Session(engine) as s:
        for t in s.scalars(select(Term)).all():
            out[t.canonical.lower()] = {
                "canonical": t.canonical,
                "category": t.category,
                "definition": t.definition,
                "why": t.why,
            }
        for a in s.scalars(select(Alias)).all():
            t = s.get(Term, a.term_id)
            if not t:
                continue
            out[a.alias.lower()] = {
                "canonical": t.canonical,
                "category": t.category,
                "definition": t.definition,
                "why": t.why,
            }
    return out

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "init":
        init_db()
        print("✅ DB initialized")
    elif cmd == "seed":
        init_db()
        seed()
        print("✅ Seeded CSVs into DB")
    elif cmd == "map":
        m = alias_to_term_map()
        print(f"Loaded {len(m)} aliases/terms")
    else:
        print("Usage: python -m app.db.repo [init|seed|map]")
