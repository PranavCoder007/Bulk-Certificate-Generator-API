from fastapi import APIRouter
from app.api.v1.jobs import router as jobs_router
from app.api.v1.certificates import router as certs_router

api_router = APIRouter()
api_router.include_router(jobs_router)
api_router.include_router(certs_router)
