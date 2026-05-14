from fastapi import APIRouter, WebSocket
from app.models.schemas import TriageSession
from app.services.graph_engine import graph_engine

router = APIRouter()

@router.post("/ingest")
async def ingest_clinical_data(data: dict):
    """
    Multimodal voice streaming and multi-turn chat ingestion.
    """
    return {"status": "received", "data": data}

@router.websocket("/stream")
async def voice_streaming(websocket: WebSocket):
    """
    WebSocket endpoint for real-time voice and chat streaming.
    """
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Processing: {data}")
