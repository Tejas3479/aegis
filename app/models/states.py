from typing import TypedDict, List, Annotated, Sequence
from typing_extensions import TypedDict
import operator

class AgentState(TypedDict):
    """
    Explicit Python TypedDict states for LangGraph orchestration.
    """
    messages: Annotated[Sequence[str], operator.add]
    patient_id: str
    triage_level: str
    symptoms_extracted: List[str]
    is_emergency: bool
    next_step: str
    clinical_notes: str
