from langgraph.graph import StateGraph, END
from app.models.states import AgentState

class GraphEngine:
    """
    Fully compiled LangGraph conversational execution engine.
    """
    def __init__(self):
        self.workflow = StateGraph(AgentState)
        self._build_graph()
        self.executor = self.workflow.compile()

    def _build_graph(self):
        """
        Defines the clinical triage workflow nodes and edges.
        """
        self.workflow.add_node("ingest", self._ingest_node)
        self.workflow.add_node("triage", self._triage_node)
        self.workflow.add_node("escalate", self._escalate_node)
        
        self.workflow.set_entry_point("ingest")
        self.workflow.add_edge("ingest", "triage")
        self.workflow.add_conditional_edges(
            "triage",
            self._should_escalate,
            {
                "emergency": "escalate",
                "normal": END
            }
        )
        self.workflow.add_edge("escalate", END)

    async def _ingest_node(self, state: AgentState):
        return {"messages": ["Ingesting data..."]}

    async def _triage_node(self, state: AgentState):
        return {"triage_level": "NORMAL"}

    async def _escalate_node(self, state: AgentState):
        return {"is_emergency": True}

    def _should_escalate(self, state: AgentState):
        return "emergency" if state.get("is_emergency") else "normal"

graph_engine = GraphEngine()
