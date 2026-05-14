import logging
from google import genai
from app.core.config import settings

logger = logging.getLogger("aegis_core")

class ModelRouter:
    """
    Intelligent multi-model LLM router with absolute failovers using Google GenAI SDK.
    """
    def __init__(self):
        self.client = genai.Client(api_key=settings.GOOGLE_GENAI_API_KEY)
        self.primary_model = "gemini-1.5-pro"
        self.fallback_model = "gemini-1.5-flash"

    async def get_response(self, prompt: str, use_pro: bool = True) -> str:
        """
        Routes query to the optimal model with absolute failover to the flash engine.
        """
        target_model = self.primary_model if use_pro else self.fallback_model
        try:
            logger.info(f"Attempting inference with {target_model}")
            response = self.client.models.generate_content(
                model=target_model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"Primary model {target_model} failed: {str(e)}. Triggering failover...")
            # Absolute failover to fallback model
            try:
                response = self.client.models.generate_content(
                    model=self.fallback_model,
                    contents=prompt
                )
                return response.text
            except Exception as fatal_e:
                logger.critical(f"Failover model {self.fallback_model} also failed: {str(fatal_e)}")
                raise fatal_e

llm_router = ModelRouter()
