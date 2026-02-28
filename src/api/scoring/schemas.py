from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict
from datetime import datetime


class ScoringBase(BaseModel):
    candidate_id: str = Field(..., description="ID кандидата")
    vacancy_id: str = Field(..., description="ID вакансии")
    match_score: float = Field(..., ge=0, le=100, description="Оценка соответствия 0-100%")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Уверенность модели (0-1)")
    analysis: Optional[Dict] = Field(None, description="Структурированный разбор")
    llm_raw_response: Optional[str] = Field(None, description="Сырой ответ LLM")


class ScoringCreate(ScoringBase):
    pass


class ScoringResponse(ScoringBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BatchScoreRequest(BaseModel):
    candidate_id: Optional[str] = Field(None, description="ID кандидата")
    vacancy_id: Optional[str] = Field(None, description="ID вакансии")
    limit: int = Field(5, ge=1, le=100, description="Лимит результатов")