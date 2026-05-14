from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict

router = APIRouter()

class AssessmentInput(BaseModel):
    answers: Dict[str, int]

@router.post("/phq-9")
async def process_phq9(assessment: AssessmentInput):
    """
    Implementation of clinical psychometric assessments (PHQ-9).
    """
    score = sum(assessment.answers.values())
    return {"assessment": "PHQ-9", "score": score, "severity": "Moderate" if score > 10 else "Low"}

@router.post("/gad-7")
async def process_gad7(assessment: AssessmentInput):
    """
    Implementation of clinical psychometric assessments (GAD-7).
    """
    score = sum(assessment.answers.values())
    return {"assessment": "GAD-7", "score": score, "severity": "Moderate" if score > 9 else "Low"}
