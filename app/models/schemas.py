from enum import Enum
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import UUID

class CareLevel(str, Enum):
    """
    Categorization of patient care priority.
    """
    HOME_CARE = "HOME_CARE"
    CLINIC_VISIT = "CLINIC_VISIT"
    EMERGENCY_ROOM = "EMERGENCY_ROOM"

class SymptomSeverity(str, Enum):
    """
    Clinical severity levels for symptom analysis.
    """
    MILD = "MILD"
    MODERATE = "MODERATE"
    CRITICAL = "CRITICAL"

class PatientVitals(BaseModel):
    """
    Validated patient vital signs monitoring.
    """
    heart_rate: Optional[int] = Field(None, ge=30, le=250)
    spO2: Optional[int] = Field(None, ge=50, le=100)
    temperature: Optional[float] = Field(None, ge=90.0, le=110.0)

class PatientProfile(BaseModel):
    """
    Consolidated medical profile and demographic data.
    """
    age: int = Field(..., ge=0, le=125)
    gender: Literal['M', 'F', 'O']
    medical_history: List[str] = Field(default_factory=list)
    vitals: Optional[PatientVitals] = None
    latitude: float
    longitude: float

class MentalHealthAssessment(BaseModel):
    """
    Clinical psychometric assessment results (PHQ-9 and GAD-7).
    """
    phq9_score: int = Field(..., ge=0, le=27)
    gad7_score: int = Field(..., ge=0, le=21)
    clinical_depression_risk: bool
    self_harm_flag: bool

class ModelEvaluationAudit(BaseModel):
    """
    Inference telemetry and audit metrics.
    """
    model_name: str
    inference_latency_ms: float
    confidence_score: float

class AIAnalysisOutput(BaseModel):
    """
    Deterministic AI-driven clinical analysis result.
    """
    extracted_symptoms: List[str]
    severity_prediction: SymptomSeverity
    care_level: CareLevel
    clinical_reasoning: str = Field(..., description="Step-by-step logic detailing why this care level fits clinical inputs.")
    guidance_notes: str = Field(..., description="Safe pre-hospitalization advice.")
    emergency_detected: bool
    risk_score: int = Field(0, ge=0, le=10) # 0-10 priority score
    mental_health_flag: bool = False
    detected_language: str

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
    care_level: Optional[CareLevel] = None
    risk_score: int = 0
    status: str = "ACTIVE"
    mental_health_flag: bool = False
    webrtc_room_url: Optional[str] = None

class TriageSession(TriageSessionBase):
    id: UUID
    updated_at: datetime

    class Config:
        from_attributes = True
