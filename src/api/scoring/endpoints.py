from fastapi import APIRouter, status, HTTPException, Query
from src.api.scoring.schemas import ScoringResponse, BatchScoreRequest, CreateScoringRequest
from src.api.scoring.dependencies import ScoringServiceDependency
from typing import List, Optional
from datetime import datetime
from fastapi.responses import StreamingResponse


router = APIRouter(prefix='/api/v1/scoring', tags=['Scoring'])

@router.post("/", response_model=ScoringResponse, status_code=status.HTTP_201_CREATED)
async def create_scoring(
    request: CreateScoringRequest,
    service: ScoringServiceDependency
):
    try:
        result = await service.calculate_match(
            candidate_id=request.candidate_id,
            vacancy_id=request.vacancy_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@router.get('/{scoring_id}', response_model=ScoringResponse)
async def get_scoring(scoring_id: str, service: ScoringServiceDependency):
    scoring = await service.get_scoring(scoring_id)
    if not scoring:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Scoring not found')
    return scoring


@router.get('/candidate/{candidate_id}', response_model=List[ScoringResponse])
async def get_candidate_scores(candidate_id: str, service: ScoringServiceDependency):
    return await service.get_candidate_scores(candidate_id)


@router.get('/vacancy/{vacancy_id}', response_model=List[ScoringResponse])
async def get_vacancy_scores(vacancy_id: str, service: ScoringServiceDependency):
    return await service.get_vacancy_scores(vacancy_id)


@router.get("/candidate/{candidate_id}/best-matches", response_model=List[ScoringResponse])
async def get_best_matches_for_candidate(
    candidate_id: str,
    service: ScoringServiceDependency,
    limit: int = Query(5, ge=1, le=20, description="Количество лучших вакансий")
):
    return await service.get_best_matches_for_candidate(candidate_id, limit=limit)


@router.get("/vacancy/{vacancy_id}/best-candidates", response_model=List[ScoringResponse])
async def get_best_candidates_for_vacancy(
    vacancy_id: str,
    service: ScoringServiceDependency,
    limit: int = Query(5, ge=1, le=20, description="Количество лучших кандидатов"),
):
    return await service.get_best_candidates_for_vacancy(vacancy_id, limit=limit)


@router.post("/batch/candidate")
async def batch_score_candidate(
    request: BatchScoreRequest,
    service: ScoringServiceDependency
):
    """Массовый скоринг кандидата по всем активным вакансиям"""
    if not request.candidate_id:
        raise HTTPException(status_code=400, detail="candidate_id is required")
    
    try:
        results = await service.batch_score_candidate(request.candidate_id)
        return {"message": f"Рассчитано {len(results)} скорингов", "count": len(results)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch/vacancy")
async def batch_score_vacancy(request: BatchScoreRequest, service: ScoringServiceDependency):
    if not request.vacancy_id:
        raise HTTPException(status_code=400, detail="vacancy_id is required")
    
    try:
        results = await service.batch_score_vacancy(request.vacancy_id)
        return {"message": f"Рассчитано {len(results)} скорингов", "count": len(results)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@router.delete('/{scoring_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_scoring(scoring_id: str, service: ScoringServiceDependency):
    deleted = await service.delete_scoring(scoring_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Scoring not found')


@router.get("/export/csv")
async def export_scores_csv(
    service: ScoringServiceDependency,
    candidate_id: Optional[str] = Query(None, description="Фильтр по ID кандидата"),
    vacancy_id: Optional[str] = Query(None, description="Фильтр по ID вакансии"),
    date_from: Optional[datetime] = Query(None, description="Дата от (ISO 8601)"),
    date_to: Optional[datetime] = Query(None, description="Дата до (ISO 8601)"),
    min_score: Optional[float] = Query(None, ge=0, le=100, description="Минимальный match_score"),
    limit: int = Query(10000, ge=1, le=100000, description="Лимит записей")
):
    try:
        csv_content = await service.export_scores_to_csv(
            candidate_id=candidate_id,
            vacancy_id=vacancy_id,
            date_from=date_from,
            date_to=date_to,
            min_score=min_score,
            limit=limit
        )
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scoring_export_{timestamp}.csv"
        
        return StreamingResponse(
            iter([csv_content.encode('utf-8-sig')]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
