import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import MentalHealthAssessment
from app.services.database import db_client

router = APIRouter()
logger = logging.getLogger("aegis_core")

@router.post("/assessment/{session_id}")
async def submit_assessment(session_id: str, assessment: MentalHealthAssessment):
    """
    Submits a formalized PHQ-9/GAD-7 assessment and updates the session flag.
    """
    try:
        # 1. Update the triage session flag
        db_client.client.table("triage_sessions")\
            .update({"mental_health_flag": True})\
            .eq("id", session_id)\
            .execute()
            
        # 2. Log assessment metrics in medical audit logs
        db_client.client.table("medical_audit_logs").insert({
            "session_id": session_id,
            "symptoms": {"mental_health": assessment.model_dump()},
            "model_metadata": {"assessment_type": "formal_psychometric"}
        }).execute()
        
        return {
            "status": "logged",
            "clinical_depression_risk": assessment.clinical_depression_risk,
            "self_harm_flag": assessment.self_harm_flag
        }
    except Exception as e:
        logger.error(f"Assessment submission failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Audit log persistence error.")
