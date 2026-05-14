import os
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from app.workers.tasks import compile_health_report

router = APIRouter()
logger = logging.getLogger("aegis_core")
REPORTS_DIR = "storage/reports"

@router.post("/generate/{session_id}")
async def trigger_report_generation(session_id: str, background_tasks: BackgroundTasks):
    """
    Triggers asynchronous EHR report compilation.
    """
    background_tasks.add_task(compile_health_report, session_id)
    return {"status": "generation_started", "session_id": session_id}

@router.get("/download/{session_id}")
async def download_health_report(session_id: str):
    """
    Serves the generated PDF health report.
    """
    file_path = os.path.join(REPORTS_DIR, f"{session_id}.pdf")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report not found or still generating.")
        
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"Aegis_Report_{session_id}.pdf"
    )

@router.get("/status/{session_id}")
async def get_report_status(session_id: str):
    """
    Checks if the report has been compiled.
    """
    file_path = os.path.join(REPORTS_DIR, f"{session_id}.pdf")
    return {"session_id": session_id, "generated": os.path.exists(file_path)}
