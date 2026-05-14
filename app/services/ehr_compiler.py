from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import aiofiles
import os

class EHRCompiler:
    """
    Streamlined ReportLab asynchronous PDF formatting engine.
    """
    async def generate_report(self, patient_id: str, triage_data: dict, output_path: str):
        """
        Asynchronously generates a medical report in PDF format.
        """
        # ReportLab itself is synchronous, we wrap it for async compatibility
        def create_pdf():
            c = canvas.Canvas(output_path, pagesize=letter)
            c.drawString(100, 750, f"Aegis Triage OS - Health Report")
            c.drawString(100, 730, f"Patient ID: {patient_id}")
            c.drawString(100, 710, f"Status: {triage_data.get('status', 'N/A')}")
            c.save()

        # Execute in thread pool or simple blocking (asyncio.to_thread in 3.9+)
        import asyncio
        await asyncio.to_thread(create_pdf)
        return output_path

ehr_compiler = EHRCompiler()
