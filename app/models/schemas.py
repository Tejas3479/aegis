from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class PatientBase(BaseModel):
    anon_hash: str
    geo_latitude: float
    geo_longitude: float

class PatientCreate(PatientBase):
    pass

class Patient(PatientBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class TriageSessionBase(BaseModel):
    patient_id: UUID
    care_level: Optional[str] = None
    status: str = "ACTIVE"
    webrtc_room_url: Optional[str] = None

class TriageSession(TriageSessionBase):
    id: UUID
    updated_at: datetime

class AuditLogCreate(BaseModel):
    session_id: UUID
    symptoms: Dict[str, Any]
    model_metadata: Dict[str, Any]

class OutbreakReport(BaseModel):
    cluster_id: int
    latitude: float
    longitude: float
    predicted_pathology: str
    density_count: int
