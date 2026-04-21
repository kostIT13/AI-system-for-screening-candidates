import httpx
import logging
from typing import Optional, List, Dict, Any


logger = logging.getLogger(__name__)


API_BASE_URL = "http://backend:8000/api/v1" 


class APIClient:
    def __init__(self, base_url: str = API_BASE_URL, timeout: float = 120.0):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=10.0, read=timeout, write=10.0), limits=httpx.Limits(max_keepalive_connections=10, max_connections=20))
        
    
    async def close(self):
        await self.client.aclose()
    
    
    async def get_candidates(
        self, 
        category: Optional[str] = None,
        location: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        params = {'limit': limit}
        if category:
            params['category'] = category
        if location:
            params['location'] = location
        
        response = await self.client.get(f"{self.base_url}/candidates/", params=params)
        response.raise_for_status()
        return response.json()
    

    async def get_candidate(self, candidate_id: str) -> Optional[Dict]:
        try:
            response = await self.client.get(f"{self.base_url}/candidates/{candidate_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    

    async def upload_candidates_csv(self, file_content: bytes, filename: str = "candidates.csv") -> Dict:
        files = {'file': (filename, file_content, 'text/csv')}
        response = await self.client.post(f"{self.base_url}/candidates/upload-csv", files=files)
        response.raise_for_status()
        return response.json()
    

    async def get_vacancies(
        self,
        category: Optional[str] = None,
        location: Optional[str] = None,
        status: Optional[str] = 'active',
        limit: int = 10
    ) -> List[Dict]:
        params = {'limit': limit, 'status': status}
        if category:
            params['category'] = category
        if location:
            params['location'] = location
        
        response = await self.client.get(f"{self.base_url}/vacancies/", params=params)
        response.raise_for_status()
        return response.json()
    

    async def get_vacancy(self, vacancy_id: str) -> Optional[Dict]:
        try:
            response = await self.client.get(f"{self.base_url}/vacancies/{vacancy_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    
    async def calculate_match(self, candidate_id: str, vacancy_id: str) -> Dict:
        payload = {'candidate_id': candidate_id, 'vacancy_id': vacancy_id}
        response = await self.client.post(f"{self.base_url}/scoring/", json=payload)
        response.raise_for_status()
        return response.json()
    

    async def get_best_matches_for_candidate(self, candidate_id: str, limit: int = 5) -> List[Dict]:
        response = await self.client.get(
            f"{self.base_url}/scoring/candidate/{candidate_id}/best",
            params={'limit': limit}
        )
        response.raise_for_status()
        return response.json()
    

    async def export_scores_csv(self, **filters) -> bytes:
        response = await self.client.get(f"{self.base_url}/scoring/export/csv", params=filters)
        response.raise_for_status()
        return response.content
    

    async def create_candidate(self, candidate_data: Dict) -> Dict:
        response = await self.client.post(f"{self.base_url}/candidates/", json=candidate_data)
        response.raise_for_status()
        return response.json()


    async def create_vacancy(self, vacancy_data: Dict) -> Dict:
        response = await self.client.post(f"{self.base_url}/vacancies/", json=vacancy_data)
        response.raise_for_status()
        return response.json()