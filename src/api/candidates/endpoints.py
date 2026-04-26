from fastapi import APIRouter, status, Query, HTTPException, UploadFile, File
from typing import List, Optional, Annotated
from src.api.candidates.schemas import CandidateResponse, CandidateCreate, CandidateUpdate, CandidateStats
from src.api.candidates.dependencies import CandidatesServiceDependency
from src.services.candidates.candidate_service import CandidateService
from src.services.candidates.parser import parse_candidates_csv


router = APIRouter(prefix="/api/v1/candidates", tags=["Candidates"])


@router.get('/', response_model=List[CandidateResponse])
async def get_candidates(
    service: CandidatesServiceDependency,
    skip: int = Query(0, ge=0, description="Пропустить N записей"),
    limit: int = Query(100, ge=1, le=1000, description="Лимит записей"),
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    location: Optional[str] = Query(None, description="Фильтр по локации"),
):
    filters = {}
    if category:
        filters['category'] = category
    if location:
        filters['location'] = location
    return await service.get_candidates(skip=skip, limit=limit, **filters)


@router.get('/{candidate_id}', response_model=CandidateResponse)
async def get_candidate(candidate_id: str, service: CandidatesServiceDependency):
    candidate = await service.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Candidate not found')
    return candidate


@router.post('/', response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def create_candidate(candidate: CandidateCreate, service: CandidatesServiceDependency):
    return await service.create_candidate(candidate.model_dump())


@router.put('/{candidate_id}', response_model=CandidateResponse)
async def update_candidate(candidate_id: str, candidate_update: CandidateUpdate, service: CandidatesServiceDependency):
    updated = await service.update_candidate(candidate_id, candidate_update.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return updated


@router.delete('/{candidate_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_candidate(candidate_id: str, service: CandidatesServiceDependency):
    deleted = await service.delete_candidate(candidate_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    

@router.post("/upload-csv")
async def upload_candidates_csv(
    service: CandidatesServiceDependency,
    file: UploadFile = File(...)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")
    
    try:
        contents = await file.read()
        parsed_candidates = await parse_candidates_csv(contents)

        count = 0
        candidate_ids = []

        for candidate_data in parsed_candidates:
            candidate = await service.create_candidate(candidate_data)
            candidate_ids.append(candidate.id)
            count += 1
        return {
            "message": f"Загружено {count} кандидатов",
            "count": count,
            "candidate_ids": candidate_ids 
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading CSV: {str(e)}")


@router.get("/stats", response_model=CandidateStats)
async def get_candidates_stats(
    service: CandidatesServiceDependency
):
    all_candidates = await service.get_candidates(limit=10000)
    
    if not all_candidates:
        return CandidateStats(
            total_count=0,
            by_category={},
            avg_experience=0.0,
            avg_salary_min=None,
            avg_salary_max=None
        )
    
    by_category = {}
    for c in all_candidates:
        by_category[c.category] = by_category.get(c.category, 0) + 1
    
    exp_list = [c.exp_years for c in all_candidates if c.exp_years]
    avg_exp = sum(exp_list) / len(exp_list) if exp_list else 0.0
   
    salary_min_list = [c.salary_min for c in all_candidates if c.salary_min]
    salary_max_list = [c.salary_max for c in all_candidates if c.salary_max]

    avg_salary_min = sum(salary_min_list) / len(salary_min_list) if salary_min_list else None
    avg_salary_max = sum(salary_max_list) / len(salary_max_list) if salary_max_list else None
    
    return CandidateStats(
        total_count=len(all_candidates),
        by_category=by_category,
        avg_experience=round(avg_exp, 2),
        avg_salary_min=round(avg_salary_min, 2) if avg_salary_min else None,
        avg_salary_max=round(avg_salary_max, 2) if avg_salary_max else None
    )


@router.get('/search/by-skill/{skill}', response_model=List[CandidateResponse])
async def get_by_skill(skill: str, service: CandidatesServiceDependency):
    return await service.get_candidates_by_skill(skill)


@router.get('/search/by-category/{category}', response_model=List[CandidateResponse])
async def get_by_category(category: str, service: CandidatesServiceDependency):
    return await service.get_candidates_by_category(category)

