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
    """
    Apply schema.sql and create ORM tables.
    """
    with engine.begin() as conn:
        if SCHEMA_PATH.exists():
            conn.execute(text(SCHEMA_PATH.read_text()))
    Base.metadata.create_all(engine)

def seed() -> None:
    """
    Load CSV seeds into Postgres.
    """
    terms_csv = DATA_DIR / "glossary_seed.csv"
    acr_csv = DATA_DIR / "acronyms_seed.csv"
    units_csv = DATA_DIR / "units_seed.csv"

    with Session(engine) as s:
        # ---- Terms ----
        if terms_csv.exists():
            with terms_csv.open(newline="") as f:
                r = csv.DictReader(f)
                for row in r:
                    canonical = row["canonical"].strip()
                    category = row["category"].strip()
                    definition = (row.get("definition") or "").strip() or None
                    why = (row.get("why") or "").strip() or None
                    alias_val = (row.get("alias") or "").strip() or None

                    term = s.scalar(select(Term).where(Term.canonical == canonical))
                    if not term:
                        term = Term(canonical=canonical, category=category,
                                    definition=definition, why=why)
                        s.add(term)
                        s.flush()

                    if alias_val:
                        exists = s.scalar(select(Alias).where(Alias.alias == alias_val))
                        if not exists:
                            s.add(Alias(term_id=term.id, alias=alias_val))

        # ---- Acronyms ----
        if acr_csv.exists():
            with acr_csv.open(newline="") as f:
                r = csv.DictReader(f)
                for row in r:
                    ac = row["acronym"].strip()
                    if not s.scalar(select(Acronym).where(Acronym.acronym == ac)):
                        expansions = [x.strip() for x in row["expansions"].split("|")]
                        clues = [seg.strip().split("/") for seg in row["clues"].split("|")]
                        s.add(Acronym(acronym=ac, expansions=expansions, clues=clues))

        # ---- Units ----
        if units_csv.exists():
            with units_csv.open(newline="") as f:
                r = csv.DictReader(f)
                for row in r:
                    u = row["unit"].strip()
                    if not s.scalar(select(Unit).where(Unit.unit == u)):
                        s.add(Unit(unit=u,
                                   canonical=row["canonical"].strip(),
                                   kind=row["kind"].strip()))
        s.commit()

def alias_to_term_map() -> dict[str, dict]:
    """
    Return { alias_lower: {canonical, category, definition, why} }
    """
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
