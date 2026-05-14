from typing import TypedDict, List, Optional, Dict, Any, Union
from uuid import UUID
from app.models.schemas import PatientProfile, AIAnalysisOutput, MentalHealthAssessment

class TriageState(TypedDict):
    """
    LangGraph persistent context state engine for conversational triage orchestration.
    """
    session_id: UUID
    profile: PatientProfile
    chat_history: List[Dict[str, str]] # Captures exact message roles (e.g., 'user', 'assistant') and content
    analysis: Optional[AIAnalysisOutput]
    mental_health_metrics: Optional[MentalHealthAssessment]
    emergency_override: bool
    telemedicine_routing_required: bool
    telemedicine_url: str
