import logging
import json
from typing import Dict, Any
from google import genai
from google.genai import types
from app.core.config import settings

from app.core.resilience import CircuitBreaker, retry_with_backoff

logger = logging.getLogger("aegis_enterprise.model_router")
router_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

class ModelRouter:
    """
    Cognitive heuristic multi-model router with absolute failovers.
    Dynamically allocates compute based on intent and clinical complexity.
    """
    
    # Static fallback matrix for clinical triage when API is unreachable
    STATIC_TRIAGE_TEMPLATE = {
        "intent": "TRIAGE",
        "detected_lang": "en",
        "complexity_score": 1.0,
        "prediction": "FALLBACK_MODE",
        "guidance": "System is in safety fallback. Please proceed with standard emergency protocols if symptoms are severe."
    }

    def __init__(self):
        try:
            self.client = genai.Client(api_key=settings.GOOGLE_GENAI_API_KEY)
            self.fast_model = "gemini-2.5-flash"
            self.pro_model = "gemini-2.5-pro"
        except Exception as e:
            logger.critical(f"GenAI Client initialization failed: {str(e)}")
            raise e

    @router_breaker
    @retry_with_backoff(retries=2)
    async def route_request(self, sanitized_text: str) -> Dict[str, Any]:
        """
        Executes fast-path analysis and routes targets to optimal compute engines.
        """
        try:
            # 1. Fast-path analysis targeting gemini-2.5-flash
            analysis_prompt = (
                f"Analyze the following medical query and return a JSON object with 'intent' (ADMIN, FAQ, or TRIAGE), "
                f"'detected_lang' (ISO code), and 'complexity_score' (float 0.0 to 1.0).\n\nQuery: {sanitized_text}"
            )
            
            # Forcing JSON schema response
            response = self.client.models.generate_content(
                model=self.fast_model,
                contents=analysis_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema={
                        "type": "OBJECT",
                        "properties": {
                            "intent": {"type": "STRING"},
                            "detected_lang": {"type": "STRING"},
                            "complexity_score": {"type": "NUMBER"}
                        },
                        "required": ["intent", "detected_lang", "complexity_score"]
                    }
                )
            )
            
            analysis = json.loads(response.text)
            intent = analysis.get("intent", "FAQ")
            complexity = analysis.get("complexity_score", 0.0)
            detected_lang = analysis.get("detected_lang", "en")
            
            translation_required = detected_lang != "en"
            
            # 2. Execution path allocation rules
            target_model = self.fast_model
            if intent == "TRIAGE" or complexity > 0.65:
                target_model = self.pro_model
                logger.info(f"Escalating request to {self.pro_model} (Complexity: {complexity})")
            else:
                logger.info(f"Routing request to {self.fast_model} (Intent: {intent})")
                
            # 3. Final model execution (scaffolded)
            # In a full implementation, this would call the target_model for the actual response
            return {
                "intent": intent,
                "complexity_score": complexity,
                "detected_lang": detected_lang,
                "translation_required": translation_required,
                "target_engine": target_model,
                "status": "routed"
            }

        except Exception as e:
            # CRITICAL STABILITY EDGE: Catch rate limits (429) or API exceptions
            logger.error(f"Routing logic failure: {str(e)}. Triggering clinical fallback matrix.")
            return self.STATIC_TRIAGE_TEMPLATE

llm_router = ModelRouter()
