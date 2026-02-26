from src.core.database import Base 
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from sqlalchemy import Integer, String, JSON
from sqlalchemy.sql import func 
from datetime import datetime
from src.models.scoring import Scoring

class Vacancies(Base):
    __tablename__ = 'vacancies'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(100), index=True)
    exp_years_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    exp_years_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    key_skills: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    location: Mapped[str] = mapped_column(String(200), index=True)
    salary_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    employment: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    remote: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='active', index=True)

    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

    scorings: Mapped[List["Scoring"]] = relationship(
        "Scoring",
        back_populates="vacancy",
        cascade="all, delete-orphan"
    )
