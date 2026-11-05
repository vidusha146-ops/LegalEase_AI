from typing import Dict
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    database_status: str
    version: str
    indian_legal_advisory: str
    helplines: Dict[str, str]
