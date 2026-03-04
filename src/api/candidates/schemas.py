from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class CandidateBase(BaseModel):
    category: str = Field(..., description="Категория (должность)")
    title: Optional[str] = Field(None, description="Заголовок")
    exp_years: Optional[int] = Field(None, description="Опыт работы (лет)")
    key_skills: Optional[List[str]] = Field(None, description="Ключевые навыки")
    location: Optional[str] = Field(None, description="Локация")
    salary_min: Optional[int] = Field(None, description="Минимальная ЗП")
    salary_max: Optional[int] = Field(None, description="Максимальная ЗП")
    employment: Optional[str] = Field(None, description="Тип занятости")
    remote: Optional[str] = Field(None, description="Удаленная работа")
    summary: Optional[str] = Field(None, description="Краткое описание")


class CandidateCreate(CandidateBase):
    pass


class CandidateUpdate(BaseModel):
    title: Optional[str] = None
    exp_years: Optional[int] = None
    key_skills: Optional[List[str]] = None
    location: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    employment: Optional[str] = None
    remote: Optional[str] = None
    summary: Optional[str] = None


class CandidateResponse(BaseModel):
    id: str 
    title: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    location: str
    created_at: datetime 
    updated_at: datetime 

    model_config = ConfigDict(from_attributes=True)


class CandidateStats(BaseModel):
    total_count: int
    by_category: dict
    avg_experience: float
    avg_salary_min: Optional[float]
    avg_salary_max: Optional[float]
