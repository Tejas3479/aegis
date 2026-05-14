import logging
from app.services.database import db_client

logger = logging.getLogger("aegis_core")

class AuditLogger:
    """
    Local database transaction ledger tracking metrics and clinical sessions via Supabase.
    """
    async def log_transaction(self, session_id: str, symptoms: dict, metadata: dict):
        """
        Persists a clinical transaction to the medical_audit_logs table.
        """
        try:
            # Execute direct insert into the audit logs table
            db_client.client.table("medical_audit_logs").insert({
                "session_id": session_id,
                "symptoms": symptoms,
                "model_metadata": metadata
            }).execute()
            logger.info(f"Audit log entry successfully persisted for session {session_id}")
        except Exception as e:
            logger.error(f"Critical failure in medical audit logging: {str(e)}")
            # In a production environment, this might trigger an external alert

audit_logger = AuditLogger()
