import logging
import os
import aiofiles
import uuid
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from google.genai import types
from app.services.model_router import llm_router
from app.services.graph_engine import graph_engine
from app.workers.tasks import compile_health_report
from app.services.pii_vault import pii_vault

router = APIRouter()
logger = logging.getLogger("aegis_core")

UPLOAD_DIR = "uploads/voice"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/voice")
async def process_voice_triage(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...)
):
    """
    Multimodal ingestion controller for voice-based triage.
    Transcribes regional dialects and pipes results into the clinical graph.
    """
    file_id = str(uuid.uuid4())
    file_ext = audio_file.filename.split(".")[-1]
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.{file_ext}")

    try:
        # 1. Stream audio data asynchronously into local file blocks
        async with aiofiles.open(file_path, 'wb') as out_file:
            while content := await audio_file.read(1024 * 64):
                await out_file.write(content)

        # 2. Send to gemini-2.5-flash with multimodal transcription instruction
        # Note: The google-genai SDK supports uploading files or passing bytes
        with open(file_path, "rb") as f:
            audio_bytes = f.read()

        transcription_prompt = (
            "Transcribe the provided audio stream with high fidelity. "
            "The user may be a patient from a rural community speaking a mixture of English "
            "and regional Indian dialects (Hinglish/Kannada-English code-switching). "
            "Accurately map the spoken symptoms to clear text while fully preserving clinical intent."
        )

        response = llm_router.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                transcription_prompt,
                types.Part.from_bytes(data=audio_bytes, mime_type=audio_file.content_type)
            ]
        )
        
        transcribed_text = response.text
        logger.info(f"Voice transcribed: {transcribed_text[:100]}...")

        # 3. Pipe payload into LangGraph pipeline
        session_id = uuid.uuid4()
        # Initializing state for the graph
        initial_state = {
            "session_id": session_id,
            "chat_history": [{"role": "user", "content": pii_vault.redact_input(transcribed_text)}],
            "profile": {}, # Placeholder or fetched from DB if patient identified
            "emergency_override": False
        }
        
        # Execute Graph (Sync wrapper for demonstration or use await if possible)
        result = await graph_engine.executor.ainvoke(initial_state, config={"configurable": {"thread_id": str(session_id)}})

        # 4. Queue background tasks
        background_tasks.add_task(compile_health_report, str(session_id))

        return {
            "session_id": session_id,
            "transcription": transcribed_text,
            "analysis": result.get("analysis"),
            "telemedicine_url": result.get("telemedicine_url"),
            "status": "processed"
        }

    except Exception as e:
        logger.error(f"Voice triage processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Voice engine ingestion exception.")
    finally:
        # Cleanup audio file if necessary
        if os.path.exists(file_path):
            os.remove(file_path)

@router.post("/chat")
async def chat_triage(data: dict, background_tasks: BackgroundTasks):
    """
    Standard text-based chat ingestion.
    """
    session_id = data.get("session_id", str(uuid.uuid4()))
    result = await graph_engine.executor.ainvoke(
        {"chat_history": [{"role": "user", "content": pii_vault.redact_input(data.get("message"))}]},
        config={"configurable": {"thread_id": session_id}}
    )
    background_tasks.add_task(compile_health_report, session_id)
    return result
