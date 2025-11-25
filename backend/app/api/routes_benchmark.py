from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.benchmark import BenchmarkService

router = APIRouter()
service = BenchmarkService()

class BenchmarkRequest(BaseModel):
    n: int

@router.post("/run")
def run_benchmark(req: BenchmarkRequest):
    if req.n < 10 or req.n > 1000000:
        raise HTTPException(status_code=400, detail="N має бути від 10 до 100 000")
    
    try:
        result = service.run_benchmark(req.n)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))