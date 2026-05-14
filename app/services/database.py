import logging
from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger("aegis_core")

class DatabaseClient:
    """
    Connection-pooled async Supabase/PostgreSQL pool client wrapper.
    """
    def __init__(self):
        self.client: Client = None

    async def connect(self):
        """
        Initializes the Supabase client connection.
        """
        try:
            self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            logger.info("Successfully connected to Supabase/PostgreSQL pool.")
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise e

    async def disconnect(self):
        """
        Cleanup database connections.
        """
        # Supabase python client doesn't require explicit close for standard REST calls,
        # but we maintain the interface for future-proofing with async pools.
        logger.info("Database client disconnected.")

db_client = DatabaseClient()
