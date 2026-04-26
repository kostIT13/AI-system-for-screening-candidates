from fastapi import APIRouter, Query, status, HTTPException, UploadFile, File, Depends
from src.api.vacancies.schemas import VacanciesResponse, VacanciesCreate, VacanciesUpdate, VacanciesStats, VacancyResponse
from typing import List, Optional
from src.api.vacancies.dependencies import VacancyServiceDependency
from src.services.vacancies.vacancies_service import VacancyService
from src.services.vacancies.parser import parse_vacancies_csv



router = APIRouter(prefix="/api/v1/vacancies", tags=["Vacancies"])


@router.get('/', response_model=List[VacancyResponse])
async def get_vacancies(
    service: VacancyServiceDependency,
    skip: int = Query(0, ge=0, description="Пропустить N записей"),
    limit: int = Query(100, ge=1, le=1000, description="Лимит записей"),
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    location: Optional[str] = Query(None, description="Фильтр по локации"),
    status: Optional[str] = Query("active", description='Фильтр по статусу')
):
    filters = {}
    if category:
        filters['category'] = category
    if location:
        filters['location'] = location
    if status:
        filters['status'] = status
    return await service.get_vacancies(skip=skip, limit=limit, **filters)


@router.get('/{vacancy_id}', response_model=VacancyResponse)
async def get_vacancy(vacancy_id: str, service: VacancyServiceDependency):
    vacancy = await service.get_vacancy(vacancy_id)
    if not vacancy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacancy not found")
    return vacancy


@router.post('/', response_model=VacancyResponse, status_code=status.HTTP_201_CREATED)
async def create_vacancy(vacancy: VacanciesCreate, service: VacancyServiceDependency):
    return await service.create_vacancy(vacancy.model_dump())


@router.put('/{vacancy_id}', response_model=VacancyResponse)
async def update_vacancy(vacancy_id: str, vacancy_update: VacanciesUpdate, service: VacancyServiceDependency):
    updated = await service.update_vacancy(vacancy_id, vacancy_update.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Vacancy not found')
    return updated


@router.delete('/{vacancy_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_vacancy(vacancy_id: str, service: VacancyServiceDependency):
    deleted = await service.delete_vacancy(vacancy_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Vacancy not found')
    

@router.post("/upload-csv")
async def upload_vacancies_csv(
        service: VacancyServiceDependency,
    file: UploadFile = File(..., description="CSV файл с вакансиями")

):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")
    
    try:
        contents = await file.read()
        parsed_vacancies = await parse_vacancies_csv(contents)

        count = 0
        for vacancy_data in parsed_vacancies:
            await service.create_vacancy(vacancy_data)
            count += 1
        
        return {"message": f"Загружено {count} вакансий", "count": count}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading CSV: {str(e)}")
    

@router.get("/stats", response_model=VacanciesStats)
async def get_vacancies_stats(
    service: VacancyServiceDependency
):
    all_vacancies = await service.get_vacancies(limit=10000)
    
    if not all_vacancies:
        return VacanciesStats(
            total_count=0,
            by_category={},
            active_count=0,
            closed_count=0,
            avg_salary_min=None,
            avg_salary_max=None
        )
    
    by_category = {}
    active_count = 0
    closed_count = 0
    
    for v in all_vacancies:
        by_category[v.category] = by_category.get(v.category, 0) + 1
        if v.status == 'active':
            active_count += 1
        elif v.status == 'closed':
            closed_count += 1

    salary_min_list = [v.salary_min for v in all_vacancies if v.salary_min]
    salary_max_list = [v.salary_max for v in all_vacancies if v.salary_max]

    avg_salary_min = sum(salary_min_list) / len(salary_min_list) if salary_min_list else None
    avg_salary_max = sum(salary_max_list) / len(salary_max_list) if salary_max_list else None
    
    return VacanciesStats(
        total_count=len(all_vacancies),
        by_category=by_category,
        active_count=active_count,
        closed_count=closed_count,
        avg_salary_min=round(avg_salary_min, 2) if avg_salary_min else None,
        avg_salary_max=round(avg_salary_max, 2) if avg_salary_max else None
    )


@router.get('/search/by-skill/{skill}', response_model=List[VacanciesResponse])
async def get_by_skill(skill: str, service: VacancyServiceDependency):
    return await service.get_vacancies_by_skill(skill)


@router.get('/search/by-category/{category}', response_model=List[VacanciesResponse])
async def get_by_category(category: str, service: VacancyServiceDependency):
    return await service.get_vacancies_by_category(category)


@router.put('/{vacancy_id}/close', response_model=VacancyResponse)
async def close_vacancy(
    vacancy_id: str,
    service: VacancyServiceDependency
):
    updated = await service.close_vacancy(vacancy_id)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacancy not found")
    return updated


@router.put('/{vacancy_id}/open', response_model=VacancyResponse)
async def open_vacancy(
    vacancy_id: str,
    service: VacancyServiceDependency
):
    updated = await service.update_vacancy(vacancy_id, {'status': 'active'})
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacancy not found")
    return updated
