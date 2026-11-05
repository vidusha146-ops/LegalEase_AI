from fastapi import APIRouter
from app.core.config import settings
from app.core.constants import LEGAL_DISCLAIMER_EN, OFFICIAL_INDIAN_HELPLINES
from app.core.database import check_db_health
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Health & Status"])


@router.get("/health", response_model=HealthResponse)
async def check_health() -> HealthResponse:
    """
    Health check endpoint returning system status, database connectivity,
    and statutory Indian legal advisory.
    """
    db_ok = await check_db_health()
    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        app_name=settings.APP_NAME,
        environment=settings.ENVIRONMENT,
        database_status="connected" if db_ok else "unreachable",
        version="1.0.0",
        indian_legal_advisory=LEGAL_DISCLAIMER_EN,
        helplines=OFFICIAL_INDIAN_HELPLINES,
    )
