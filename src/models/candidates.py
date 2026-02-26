from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database import Base
from sqlalchemy import String, Integer, JSON
from sqlalchemy.sql import func
from typing import List, Optional
from src.models.scoring import Scoring
from datetime import datetime


class Candidates(Base):
    __tablename__ = "candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(100), index=True)
    exp_years: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    key_skills: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    location: Mapped[str] = mapped_column(String(200), index=True)
    salary_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    employment: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    remote: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

    scorings: Mapped[List["Scoring"]] = relationship("Scoring", back_populates="candidate", cascade="all, delete-orphan")
