# app/db/models.py

from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, CheckConstraint, JSON, TIMESTAMP
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

# <-- THIS is the "Base" your repo imports -->
Base = declarative_base()

class Term(Base):
    __tablename__ = "terms"
    id = Column(Integer, primary_key=True, index=True)
    canonical = Column(Text, nullable=False)
    category = Column(
        String,
        CheckConstraint("category IN ('diagnosis','procedure','medication','test','anatomy','measurement')"),
        nullable=False,
    )
    definition = Column(Text)
    why = Column(Text)

    aliases = relationship("Alias", back_populates="term", cascade="all, delete-orphan")

class Alias(Base):
    __tablename__ = "aliases"
    id = Column(Integer, primary_key=True, index=True)
    term_id = Column(Integer, ForeignKey("terms.id", ondelete="CASCADE"), nullable=False)
    alias = Column(Text, unique=True, nullable=False)

    term = relationship("Term", back_populates="aliases")

class Acronym(Base):
    __tablename__ = "acronyms"
    id = Column(Integer, primary_key=True, index=True)
    acronym = Column(String, unique=True, nullable=False)
    expansions = Column(JSON, nullable=False)   # list[str]
    clues = Column(JSON, nullable=False)        # list[list[str]]

class Unit(Base):
    __tablename__ = "units"
    id = Column(Integer, primary_key=True, index=True)
    unit = Column(String, unique=True, nullable=False)
    canonical = Column(String, nullable=False)
    kind = Column(String, nullable=False)

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    doc_uuid = Column(String, nullable=False)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

class Metric(Base):
    __tablename__ = "metrics"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    value = Column(String, nullable=False)
    at = Column(TIMESTAMP, server_default=func.now())
