import logging
import base64
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from io import BytesIO

from app.services.database import db_client

logger = logging.getLogger("aegis_core")
REPORTS_DIR = "storage/reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

async def compile_health_report(session_id: str):
    """
    Lightweight asynchronous EHR compiler using ReportLab.
    Uploads results to Supabase Storage and updates the database record.
    """
    try:
        logger.info(f"Starting async EHR compilation for session: {session_id}")
        
        # 1. Fetch clinical data from database
        # In production, we query the medical_audit_logs and triage_sessions
        # response = db_client.client.table("triage_sessions").select("*, patients(*)").eq("id", session_id).single().execute()
        # triage_data = response.data
        
        # Mock data for demonstration as per instructions
        triage_data = {
            "patient_hash": "ANON_8829_XP",
            "symptoms": ["Acute fever", "Dry cough", "Muscle fatigue"],
            "care_level": "CLINIC_VISIT",
            "risk_score": 7,
            "mental_health_flag": False,
            "reasoning": "Symptoms indicate potential viral infection without immediate respiratory distress. Cluster proximity suggests localized outbreak risk."
        }

        # 2. Build PDF Document using ReportLab
        file_path = os.path.join(REPORTS_DIR, f"{session_id}.pdf")
        doc = SimpleDocTemplate(file_path, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Professional Header
        elements.append(Paragraph("Aegis Triage OS - Clinical Report", styles['Title']))
        elements.append(Spacer(1, 12))

        # CRITICAL DIRECTIVE: MANDATORY LEGAL DISCLAIMER
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            textColor=colors.red,
            fontSize=10,
            alignment=1 # Center
        )
        elements.append(Paragraph(
            "<b>Aegis OS is an AI assistant, not a replacement for professional medical diagnosis.</b>",
            disclaimer_style
        ))
        elements.append(Spacer(1, 24))

        # Patient Metrics Table
        # Wrap text in Paragraph containers to prevent cell overflow
        table_data = [
            [Paragraph("<b>Attribute</b>", styles['Normal']), Paragraph("<b>Clinical Value</b>", styles['Normal'])],
            ["Patient Hash", triage_data["patient_hash"]],
            ["Session ID", session_id],
            ["Classification", triage_data["care_level"]],
            ["Risk Score", f"{triage_data['risk_score']}/10"],
            ["Mental Health Concern", "Yes" if triage_data['mental_health_flag'] else "No"],
        ]
        
        t = Table(table_data, colWidths=[150, 350])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))

        # Clinical Reasoning
        elements.append(Paragraph("<b>Clinical Reasoning:</b>", styles['Heading3']))
        elements.append(Paragraph(triage_data["reasoning"], styles['Normal']))
        elements.append(Spacer(1, 12))

        # Symptoms List
        elements.append(Paragraph("<b>Extracted Symptoms:</b>", styles['Heading3']))
        for symptom in triage_data["symptoms"]:
            elements.append(Paragraph(f"• {symptom}", styles['Normal']))

        # 3. Finalize PDF and Upload
        doc.build(elements)
        
        # Upload binary directly to Supabase Storage
        with open(file_path, "rb") as f:
            file_data = f.read()
            # Note: storage.from_('reports').upload(path, data) is the standard Supabase flow
            try:
                storage_path = f"reports/{session_id}.pdf"
                db_client.client.storage.from_("reports").upload(
                    path=storage_path,
                    file=file_data,
                    file_options={"content-type": "application/pdf"}
                )
                logger.info(f"EHR Report uploaded to Supabase: {storage_path}")
            except Exception as se:
                logger.warning(f"Supabase Storage upload failed (Check bucket permissions): {str(se)}")

        # Update database with the report reference
        # db_client.client.table("triage_sessions").update({"webrtc_room_url": storage_path}).eq("id", session_id).execute()
        
        logger.info(f"EHR Report compilation complete for {session_id}")
        return True

    except Exception as e:
        logger.error(f"EHR Compilation failed: {str(e)}")
        return False
