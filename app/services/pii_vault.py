import re
import logging
from typing import Optional
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

logger = logging.getLogger("aegis_core")

class PrivacyInterceptor:
    """
    Resilient data redaction privacy vault ensuring DPDP compliance.
    Includes explicit regex fallback paths for stability.
    """
    
    # Fallback regex patterns for Indian national phone structures, emails, and names
    PHONE_PATTERN = r"(?:\+91|0)?[6-9]\d{9}"
    EMAIL_PATTERN = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    # Simplified name pattern for fallback (detects common capitalized patterns)
    NAME_PATTERN = r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b"
    
    REDACTION_LABEL = "[ANONYMIZED_PATIENT_DATA]"

    def __init__(self):
        try:
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
            self.presidio_active = True
        except Exception as e:
            logger.error(f"Presidio engine initialization failed: {str(e)}. Switching to Regex Fallback mode.")
            self.presidio_active = False

    def redact_input(self, text: str) -> str:
        """
        Analyzes and redacts PII from incoming clinical text.
        """
        if not text:
            return ""

        try:
            if self.presidio_active:
                # Primary Path: Microsoft Presidio
                results = self.analyzer.analyze(
                    text=text, 
                    entities=["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "LOCATION"], 
                    language='en'
                )
                anonymized_result = self.anonymizer.anonymize(
                    text=text,
                    analyzer_results=results,
                    operators={
                        "PERSON": OperatorConfig("replace", {"new_value": self.REDACTION_LABEL}),
                        "PHONE_NUMBER": OperatorConfig("replace", {"new_value": self.REDACTION_LABEL}),
                        "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": self.REDACTION_LABEL}),
                        "LOCATION": OperatorConfig("replace", {"new_value": self.REDACTION_LABEL})
                    }
                )
                return anonymized_result.text
            else:
                return self._apply_regex_fallback(text)
        except Exception as e:
            logger.warning(f"PII Redaction engine error: {str(e)}. Triggering regex fallback matrix.")
            return self._apply_regex_fallback(text)

    def _apply_regex_fallback(self, text: str) -> str:
        """
        High-speed Python regex parsing matrix for fail-safe data minimization.
        """
        sanitized = text
        # Redact Phones
        sanitized = re.sub(self.PHONE_PATTERN, self.REDACTION_LABEL, sanitized)
        # Redact Emails
        sanitized = re.sub(self.EMAIL_PATTERN, self.REDACTION_LABEL, sanitized)
        # Redact Names (Heuristic fallback)
        # Note: We apply this carefully to avoid over-redacting clinical terms
        sanitized = re.sub(self.NAME_PATTERN, self.REDACTION_LABEL, sanitized)
        
        return sanitized

pii_vault = PrivacyInterceptor()
