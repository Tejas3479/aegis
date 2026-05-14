import logging
import asyncio
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
        Initializes the Supabase client connection with enterprise-grade retries.
        """
        retries = 3
        for i in range(retries):
            try:
                self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                logger.info("Successfully connected to Supabase/PostgreSQL pool.")
                return
            except Exception as e:
                if i == retries - 1:
                    logger.critical(f"Final database connection attempt failed: {str(e)}")
                    raise e
                wait = (i + 1) * 2
                logger.warning(f"Database connection attempt {i+1} failed. Retrying in {wait}s...")
                await asyncio.sleep(wait)

    async def disconnect(self):
        """
        Cleanup database connections.
        """
        # Supabase python client doesn't require explicit close for standard REST calls,
        # but we maintain the interface for future-proofing with async pools.
        logger.info("Database client disconnected.")

db_client = DatabaseClient()
