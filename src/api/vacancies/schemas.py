from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List 
from datetime import datetime


class VacanciesBase(BaseModel):
    category: str = Field(..., description="Категория (должность)")
    title: Optional[str] = Field(None, description="Заголовок")
    exp_years_min: Optional[int] = Field(None, description="Минимальный опыт (лет)")
    exp_years_max: Optional[int] = Field(None, description="Максимальный опыт (лет)")
    key_skills: Optional[List[str]] = Field(None, description="Ключевые навыки")
    location: Optional[str] = Field(None, description="Локация")
    salary_min: Optional[int] = Field(None, description="Минимальная ЗП")
    salary_max: Optional[int] = Field(None, description="Максимальная ЗП")
    employment: Optional[str] = Field(None, description="Тип занятости")
    remote: Optional[str] = Field(None, description="Удаленная работа")
    summary: Optional[str] = Field(None, description="Краткое описание")
    status: Optional[str] = Field(None, description="Статус вакансии")


class VacanciesCreate(VacanciesBase):
    pass 


class VacanciesUpdate(BaseModel):
    title: Optional[str] = None
    exp_years_min: Optional[int] = None
    exp_years_max: Optional[int] = None
    key_skills: Optional[List[str]] = None
    location: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    employment: Optional[str] = None
    remote: Optional[str] = None
    summary: Optional[str] = None
    status: Optional[str] = None


class VacancyResponse(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime
    
    category: str
    title: str
    exp_years_min: Optional[int] = None
    exp_years_max: Optional[int] = None
    key_skills: Optional[List[str]] = None
    location: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    employment: Optional[str] = None
    remote: Optional[str] = None
    summary: Optional[str] = None
    status: str = 'active'
    
    model_config = ConfigDict(from_attributes=True)
    

class VacanciesResponse(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VacanciesStats(BaseModel):
    total_count: int
    by_category: dict
    active_count: int
    closed_count: int
    avg_salary_min: Optional[float]
    avg_salary_max: Optional[float]

