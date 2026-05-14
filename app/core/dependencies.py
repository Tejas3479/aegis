from fastapi import Header, HTTPException, Depends
from typing import Annotated
from app.core.config import settings

async def verify_api_key(x_api_key: Annotated[str, Header()] = None):
    """
    Global middleware interceptor for API key validation.
    """
    if not x_api_key:
        raise HTTPException(status_code=403, detail="Missing API Key")
    # Add validation logic here
    return x_api_key

async def get_current_patient_id(patient_id: str):
    """
    Dependency to isolate and validate patient scope.
    """
    if not patient_id:
        raise HTTPException(status_code=400, detail="Patient ID required")
    return patient_id
