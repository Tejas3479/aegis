import hmac
import hashlib
import logging
from fastapi import APIRouter, Header, HTTPException, Request
from typing import Annotated, Dict, Any
from app.core.config import settings
from app.services.graph_engine import graph_engine
from app.services.database import db_client
from app.models.schemas import CareLevel

router = APIRouter()
logger = logging.getLogger("aegis_core")

@router.post("/webhook")
async def receive_vital_monitoring(
    request: Request,
    payload: dict,
    x_signature: Annotated[str, Header()] = None
):
    """
    Cryptographically signed webhook receivers for vital monitoring.
    Verifies HMAC-SHA256 signatures for production security.
    """
    if not x_signature:
        raise HTTPException(status_code=401, detail="Missing cryptographic signature")
    
    # 1. Verification Logic
    body = await request.body()
    expected_signature = hmac.new(
        settings.SECRET_KEY.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, x_signature):
        logger.warning(f"Invalid webhook signature attempt from {request.client.host}")
        raise HTTPException(status_code=403, detail="Invalid cryptographic signature")
    
    # 2. Process Vitals (Scaffolded)
    logger.info(f"Vitals received for patient: {payload.get('patient_id')}")
    return {"status": "verified_and_processed", "vitals_received": True}

@router.post("/sync")
async def sync_wearable_data(payload: Dict[str, Any]):
    """
    Advanced Wearables Integration: Syncs real-time vitals into the active LangGraph state.
    Triggers immediate clinical interception for critical thresholds.
    """
    session_id = payload.get("session_id")
    heart_rate = payload.get("heart_rate")
    spO2 = payload.get("spO2")

    if not all([session_id, heart_rate, spO2]):
        raise HTTPException(status_code=400, detail="Missing required vitals: session_id, heart_rate, spO2")

    try:
        # 1. Programmatically update LangGraph thread state
        thread_config = {"configurable": {"thread_id": session_id}}
        updated_profile = {
            "vitals": {
                "heart_rate": heart_rate,
                "spO2": spO2
            }
        }
        
        # Intercept logic for critical thresholds
        emergency_triggered = False
        if heart_rate > 120 or spO2 < 92:
            logger.warning(f"CRITICAL VITALS DETECTED for session {session_id}: HR={heart_rate}, spO2={spO2}")
            emergency_triggered = True
            
            # Update DB triage session to EMERGENCY_ROOM
            db_client.client.table("triage_sessions")\
                .update({"care_level": CareLevel.EMERGENCY_ROOM, "risk_score": 10})\
                .eq("id", session_id)\
                .execute()
            
            # Inject emergency flag into the graph state
            graph_engine.executor.update_state(
                thread_config, 
                {"profile": updated_profile, "emergency_override": True}
            )
        else:
            # Standard state update
            graph_engine.executor.update_state(
                thread_config, 
                {"profile": updated_profile}
            )

        return {
            "status": "synchronized",
            "emergency_detected": emergency_triggered,
            "session_id": session_id
        }

    except Exception as e:
        logger.error(f"Wearable sync failure: {str(e)}")
        raise HTTPException(status_code=500, detail="Vitals synchronization exception.")
