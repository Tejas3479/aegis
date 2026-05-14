import logging
from fastapi import APIRouter, HTTPException
from typing import List
from app.services.database import db_client
from app.models.schemas import TriageSession

router = APIRouter()
logger = logging.getLogger("aegis_core")

@router.get("/queue", response_model=List[TriageSession])
async def get_priority_queue():
    """
    Retrieves the clinical priority queue sorted by risk_score and care_level.
    """
    try:
        # Sort by risk_score (desc) and updated_at (asc)
        response = db_client.client.table("triage_sessions")\
            .select("*")\
            .filter("status", "eq", "ACTIVE")\
            .order("risk_score", desc=True)\
            .order("updated_at", desc=False)\
            .execute()
        
        return response.data
    except Exception as e:
        logger.error(f"Failed to fetch priority queue: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal queue synchronization error.")

@router.post("/route-session/{session_id}")
async def route_webrtc_session(session_id: str):
    """
    Triggers WebRTC session routing and updates session status to ESCALATED.
    """
    try:
        room_url = f"https://webrtc.aegis.os/{session_id}"
        
        # Update database with the room URL and new status
        db_client.client.table("triage_sessions")\
            .update({"webrtc_room_url": room_url, "status": "ESCALATED"})\
            .eq("id", session_id)\
            .execute()
            
        return {"status": "routed", "room_url": room_url}
    except Exception as e:
        logger.error(f"Routing failure for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Telemedicine routing exception.")
