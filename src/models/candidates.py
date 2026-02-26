# src/models/candidates.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database import Base
from sqlalchemy import String, Integer, Date, Boolean, JSON, Text, DateTime, Float, Index
from sqlalchemy.sql import func
from typing import List, Optional
from src.models.scoring import Scoring


class Candidates(Base):
    __tablename__ = "candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True, comment="UUID кандидата")
    gender: Mapped[Optional[str]] = mapped_column(String(20), comment="Пол: male/female")
    age: Mapped[Optional[int]] = mapped_column(Integer, comment="Возраст в годах")
    birth_day: Mapped[Optional[Date]] = mapped_column(Date, comment="Дата рождения")
    expected_salary: Mapped[Optional[int]] = mapped_column(Integer, comment="Ожидаемая ЗП в рублях")
    currency: Mapped[str] = mapped_column(String(3), default="RUB", comment="Валюта ЗП")
    target_position: Mapped[Optional[str]] = mapped_column(String(200), index=True, comment="Искомая должность")
    city: Mapped[Optional[str]] = mapped_column(String(150), comment="Город проживания")
    region: Mapped[Optional[str]] = mapped_column(String(100), comment="Область/регион (например, Калининградская область)")
    ready_to_relocate: Mapped[bool] = mapped_column(Boolean, default=False, comment="Готов к переезду")
    ready_for_business_trips: Mapped[bool] = mapped_column(Boolean, default=False, comment="Готов к командировкам")
    employment_types: Mapped[Optional[List[str]]] = mapped_column(
        JSON, 
        default=list,
        comment="Типы занятости: ['частичная', 'полная']"
    )
    schedule_preferences: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        default=list,
        comment="Графики"
    )
    work_experience: Mapped[Optional[List[dict]]] = mapped_column(
        JSON,
        default=list,
        comment="""
        Список мест работы:
        [
            {
                "company": "МАОУ СОШ №1 г.Немана",
                "position": "Системный администратор",
                "start_date": "2010-08",
                "end_date": null,
                "duration": "8 лет 10 месяцев",
                "description": "Обслуживание ПК, установка ПО..."
            }
        ]
        """
    )
    total_experience_years: Mapped[Optional[float]] = mapped_column(
        Float, 
        comment="Общий опыт в годах (вычисляемый)"
    )
    current_employer: Mapped[Optional[str]] = mapped_column(String(200), comment="Последний работодатель")
    current_position: Mapped[Optional[str]] = mapped_column(String(200), comment="Последняя должность")
    education: Mapped[Optional[dict]] = mapped_column(
        JSON,
        default=dict,
        comment="""
        {
            "level": "incomplete_higher",
            "university": "Балтийская государственная академия рыбопромыслового флота",
            "city": "Калининград",
            "faculty": "судоводительский",
            "specialty": "Организация и безопасность движения",
            "graduation_year": 2000
        }
        """
    )
    resume_updated_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime,
        comment="Дата обновления резюме в источнике (например, 16.04.2019 15:59)"
    )
    has_car: Mapped[bool] = mapped_column(Boolean, default=False, comment="Имеется собственный автомобиль")
    skills: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        default=list,
        comment="Навыки"
    )
    about: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Дополнительная информация / о себе"
    )
    ai_score: Mapped[Optional[float]] = mapped_column(
        Float,
        index=True,
        comment="Оценка соответствия вакансии (0-100%), рассчитанная AI"
    )
    ai_analysis: Mapped[Optional[dict]] = mapped_column(
        JSON,
        comment="""
        Детальный анализ от AI:
        {
            "match_reasons": ["Опыт в IT", "Системное администрирование"],
            "gaps": ["Нет высшего образования"],
            "confidence": 0.87,
            "recommendation": "Рекомендован к собеседованию"
        }
        """
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now(),
        comment="Дата создания записи в БД"
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Дата последнего обновления записи"
    )
    
    scores: Mapped[List["Scoring"]] = relationship(
        "Scoring", 
        back_populates="candidate",
        cascade="all, delete-orphan"
    )

