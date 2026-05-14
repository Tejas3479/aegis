import re

class Gatekeeper:
    """
    Deterministic regex logic for clinical bypass events.
    """
    EMERGENCY_KEYWORDS = [
        r"chest\s*pain",
        r"difficulty\s*breathing",
        r"severe\s*bleeding",
        r"unconscious",
        r"stroke\s*symptoms"
    ]

    def check_for_bypass(self, input_text: str) -> bool:
        """
        Scans input for life-critical keywords to trigger immediate clinical bypass.
        """
        for pattern in self.EMERGENCY_KEYWORDS:
            if re.search(pattern, input_text, re.IGNORECASE):
                return True
        return False

gatekeeper = Gatekeeper()
