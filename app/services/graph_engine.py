import logging
import uuid
import re
import json
from typing import Dict, Any, List, Union
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from google.genai import types

from app.models.states import TriageState
from app.models.schemas import AIAnalysisOutput, MentalHealthAssessment, CareLevel, SymptomSeverity
from app.services.model_router import llm_router
from app.harness.gatekeeper import gatekeeper
from app.services.pii_vault import pii_vault

logger = logging.getLogger("aegis_core")

class GraphEngine:
    """
    Fully compiled LangGraph conversational execution engine for Aegis Triage OS.
    Implements multi-turn clinical reasoning with deterministic safety rails.
    """

    def __init__(self):
        self.memory = MemorySaver()
        self.workflow = StateGraph(TriageState)
        self._build_graph()
        self.executor = self.workflow.compile(checkpointer=self.memory)

    def _build_graph(self):
        """
        Defines the clinical triage workflow nodes, edges, and conditional paths.
        """
        # 1. Add Nodes
        self.workflow.add_node("context_builder", self.context_builder)
        self.workflow.add_node("clinical_analyzer", self.clinical_analyzer)
        self.workflow.add_node("mental_health_assessor", self.mental_health_assessor)
        self.workflow.add_node("risk_scoring_gatekeeper", self.risk_scoring_gatekeeper)
        self.workflow.add_node("telemedicine_provisioner", self.telemedicine_provisioner)
        self.workflow.add_node("guidance_generator", self.guidance_generator)
        self.workflow.add_node("translator", self.translator)

        # 2. Establish Structural Paths
        self.workflow.set_entry_point("context_builder")
        self.workflow.add_edge("context_builder", "clinical_analyzer")
        self.workflow.add_edge("clinical_analyzer", "mental_health_assessor")
        self.workflow.add_edge("mental_health_assessor", "risk_scoring_gatekeeper")

        # 3. Conditional Routing Logic
        self.workflow.add_conditional_edges(
            "risk_scoring_gatekeeper",
            self._route_post_risk_gate,
            {
                "emergency": "telemedicine_provisioner",
                "standard": "guidance_generator"
            }
        )

        self.workflow.add_edge("guidance_generator", "telemedicine_provisioner")
        self.workflow.add_edge("telemedicine_provisioner", "translator")
        self.workflow.add_edge("translator", END)

    # --- Node Implementations ---

    async def context_builder(self, state: TriageState) -> Dict[str, Any]:
        """
        Aggregates active user messages, history, and patient profile into a clinical prompt.
        """
        history_str = "\n".join([f"{m['role']}: {m['content']}" for m in state.get("chat_history", [])])
        profile = state.get("profile")
        
        clinical_dossier = f"""
        [PATIENT PROFILE]
        Age: {profile.age}
        Gender: {profile.gender}
        History: {', '.join(profile.medical_history)}
        Vitals: {profile.vitals.model_dump() if profile.vitals else 'N/A'}
        
        [CONVERSATIONAL HISTORY]
        {pii_vault.redact_input(history_str)}
        """
        return {"context_string": clinical_dossier}

    async def clinical_analyzer(self, state: TriageState) -> Dict[str, Any]:
        """
        Interfaces with gemini-2.5-pro to extract symptoms and categorize risk severity.
        """
        dossier = state.get("context_string")
        system_prompt = """
        You are the automated diagnostic framework of Aegis Triage OS. Review the aggregated clinical dossier.
        Extract present conditions into 'extracted_symptoms'. Categorize risk severity precisely.
        Assign a 'risk_score' (integer 0-10) where 10 is the highest clinical urgency.
        You must output an immutable schema structured identically to AIAnalysisOutput.
        If the user expresses acute psychometric trauma or indicators of dangerous physical degradation, flag emergency_detected=True immediately.
        Explain your decisions in full under 'clinical_reasoning' to maintain total algorithmic transparency.
        """
        
        try:
            # Enforce structured output via the router
            response = llm_router.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=f"{system_prompt}\n\nClinical Dossier:\n{dossier}",
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AIAnalysisOutput.model_json_schema()
                )
            )
            analysis_data = json.loads(response.text)
            analysis = AIAnalysisOutput(**analysis_data)
            return {"analysis": analysis}
        except Exception as e:
            logger.error(f"Clinical analysis failure: {str(e)}")
            # Fail-safe minimal analysis
            return {"analysis": AIAnalysisOutput(
                extracted_symptoms=[], 
                severity_prediction=SymptomSeverity.MODERATE, 
                care_level=CareLevel.CLINIC_VISIT,
                clinical_reasoning="System fail-safe triggered due to inference error.",
                guidance_notes="Please consult a professional immediately.",
                emergency_detected=False,
                detected_language="en"
            )}

    async def mental_health_assessor(self, state: TriageState) -> Dict[str, Any]:
        """
        Analyzes for psychometric distress and maps to PHQ-9/GAD-7 metrics.
        """
        chat_text = " ".join([m['content'] for m in state.get("chat_history", [])]).lower()
        distress_keywords = ["hopeless", "worthless", "harm", "end it", "depressed", "anxious"]
        
        is_distressed = any(k in chat_text for k in distress_keywords)
        
        # Heuristic scoring for demonstration
        phq9 = 16 if "hopeless" in chat_text or "end it" in chat_text else 5
        gad7 = 15 if "anxious" in chat_text else 4
        
        mh_assessment = MentalHealthAssessment(
            phq9_score=phq9,
            gad7_score=gad7,
            clinical_depression_risk=phq9 >= 15 or gad7 >= 15,
            self_harm_flag="end it" in chat_text or "harm" in chat_text
        )

        updates = {"mental_health_metrics": mh_assessment}
        
        # Elevate care tier and set mental health flag if scoring is high
        if mh_assessment.clinical_depression_risk or mh_assessment.self_harm_flag:
            analysis = state.get("analysis")
            if analysis:
                analysis.care_level = CareLevel.EMERGENCY_ROOM if mh_assessment.self_harm_flag else CareLevel.CLINIC_VISIT
                analysis.mental_health_flag = True
                analysis.risk_score = max(analysis.risk_score, 8 if mh_assessment.self_harm_flag else 5)
                updates["analysis"] = analysis
                
        return updates

    async def risk_scoring_gatekeeper(self, state: TriageState) -> Dict[str, Any]:
        """
        Deterministic safety rules to scan for acute crises independent of the model.
        """
        chat_text = " ".join([m['content'] for m in state.get("chat_history", [])]).lower()
        analysis = state.get("analysis")
        
        # Regex patterns for acute crises
        CRISIS_PATTERNS = [
            r"crushing\s*chest\s*pain",
            r"sudden\s*paralysis",
            r"cannot\s*breathe",
            r"stroke\s*symptoms"
        ]
        
        found_crisis = any(re.search(p, chat_text) for p in CRISIS_PATTERNS)
        model_flag = analysis.emergency_detected if analysis else False
        
        if found_crisis or model_flag:
            logger.warning("CRITICAL RISK DETECTED: Overriding workflow to EMERGENCY_ROOM.")
            if analysis:
                analysis.care_level = CareLevel.EMERGENCY_ROOM
                analysis.emergency_detected = True
                analysis.risk_score = 10 # Maximum urgency
            return {
                "emergency_override": True,
                "analysis": analysis
            }
        
        return {"emergency_override": False}

    async def telemedicine_provisioner(self, state: TriageState) -> Dict[str, Any]:
        """
        Generates active video signaling room for emergency cases.
        """
        analysis = state.get("analysis")
        if state.get("emergency_override") or (analysis and analysis.care_level == CareLevel.EMERGENCY_ROOM):
            room_uuid = str(uuid.uuid4())
            return {
                "telemedicine_routing_required": True,
                "telemedicine_url": f"https://telemed.aegis.os/room/{room_uuid}"
            }
        return {"telemedicine_routing_required": False, "telemedicine_url": ""}

    async def guidance_generator(self, state: TriageState) -> Dict[str, Any]:
        """
        Compiles safe monitoring guidelines for non-emergency home care.
        """
        analysis = state.get("analysis")
        if analysis and analysis.care_level == CareLevel.HOME_CARE:
            prompt = f"Generate 3 safe monitoring guidelines for symptoms: {', '.join(analysis.extracted_symptoms)}"
            try:
                response = llm_router.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                analysis.guidance_notes = response.text
                return {"analysis": analysis}
            except Exception:
                return {}
        return {}

    async def translator(self, state: TriageState) -> Dict[str, Any]:
        """
        Translates final response text if dialect parameters are active.
        """
        # Scaffold for translation logic
        return {}

    # --- Helper Logic ---

    def _route_post_risk_gate(self, state: TriageState):
        """
        Conditional routing logic based on emergency status.
        """
        analysis = state.get("analysis")
        if state.get("emergency_override") or (analysis and analysis.care_level == CareLevel.EMERGENCY_ROOM):
            return "emergency"
        return "standard"

graph_engine = GraphEngine()
