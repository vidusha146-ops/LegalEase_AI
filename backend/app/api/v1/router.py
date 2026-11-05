from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.statutes import router as statutes_router
from app.api.v1.analyzer import router as analyzer_router
from app.api.v1.evidence import router as evidence_router, timeline_router
from app.api.v1.drafts import router as drafts_router
from app.api.v1.cases import router as cases_router
from app.api.v1.multilingual import router as multilingual_router
from app.api.v1.dashboard import router as dashboard_router

api_v1_router = APIRouter()

# Include Sub-Routers
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(statutes_router)
api_v1_router.include_router(analyzer_router)
api_v1_router.include_router(evidence_router)
api_v1_router.include_router(timeline_router)
api_v1_router.include_router(drafts_router)
api_v1_router.include_router(cases_router)
api_v1_router.include_router(multilingual_router)
api_v1_router.include_router(dashboard_router)
