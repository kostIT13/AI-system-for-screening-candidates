from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database import Base
from sqlalchemy import String, Integer, Float, JSON, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from typing import Optional
from src.models.candidates import Candidates
from src.models.vacancies import Vacancies


class Scoring(Base):
    __tablename__ = "scoring"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    candidate_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        index=True,
        comment="ID кандидата"
    )
    vacancy_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("vacancies.id", ondelete="CASCADE"),
        index=True,
        comment="ID вакансии"
    )
    match_score: Mapped[float] = mapped_column(
        Float,
        comment="Оценка соответствия 0-100%"
    )
    confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Уверенность модели в оценке (0-1)"
    )
    analysis: Mapped[Optional[dict]] = mapped_column(
        JSON,
        comment="Структурированный разбор: сильные стороны, пробелы, рекомендации"
    )
    llm_raw_response: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Сырой ответ от LLM (для отладки и аудита)"
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now(),
        comment="Дата расчёта скоринга"
    )
    candidate: Mapped["Candidates"] = relationship(
        "Candidates",
        back_populates="scorings",
        lazy='selectin'
    )
    vacancy: Mapped["Vacancies"] = relationship(
        "Vacancies",
        back_populates="scorings",
        lazy="selectin"
    )
