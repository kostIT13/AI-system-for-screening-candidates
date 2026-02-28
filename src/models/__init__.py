from src.models.candidates import Candidates 
from src.models.vacancies import Vacancies   
from src.models.scoring import Scoring       
from src.core.database import Base

__all__ = ["Base", "Candidates", "Vacancies", "Scoring"]