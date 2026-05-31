"""
graph.py — Construction du graphe LangGraph pour LangGraph Studio.

Workflow :
  START → Supervisor → DiagnosticAgent (boucle 5 questions)
        → Supervisor → PhysicianReview (Human-in-the-Loop)
        → Supervisor → ReportAgent → END
"""
import logging
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from .state import ClinicalWorkflowState
from .nodes.supervisor import supervisor_node, route_after_supervisor
from .nodes.diagnostic_agent import diagnostic_agent_node
from .nodes.physician_review import physician_review_node
from .nodes.report_agent import report_agent_node

logger = logging.getLogger(__name__)


# ── Fonctions de routage conditionnel ────────────────────────────────────────

def route_after_diagnostic(state: ClinicalWorkflowState) -> str:
    """
    Après DiagnosticAgent :
    - Si la synthèse est prête  → retour au Supervisor (qui ira vers PhysicianReview)
    - Sinon (encore des questions) → END (attend la prochaine réponse patient)
    """
    ws = state.get("workflow_status", "")
    next_step = state.get("next_step", "")

    if ws == "awaiting_physician" or next_step == "physician_review":
        logger.info("[Route:diagnostic] → supervisor (synthèse prête)")
        return "supervisor"

    logger.info("[Route:diagnostic] → END (attente réponse patient)")
    return END


def route_after_physician(state: ClinicalWorkflowState) -> str:
    """
    Après PhysicianReview :
    - Si la validation médecin est présente → ReportAgent
    - Sinon → END (attente de la saisie médecin)
    """
    if state.get("next_step") == "report_agent":
        logger.info("[Route:physician] → report_agent")
        return "report_agent"
    logger.info("[Route:physician] → END (attente médecin)")
    return END


# ── Construction du graphe ────────────────────────────────────────────────────

def build_clinical_graph() -> StateGraph:
    """
    Construit et compile le graphe LangGraph du workflow clinique.

    Nœuds :
      - supervisor        : orchestre le workflow
      - diagnostic_agent  : pose 5 questions + génère la synthèse (via LLM + MCP)
      - physician_node    : étape Human-in-the-Loop (interruption avant ce nœud)
      - report_agent      : génère le rapport final structuré

    L'interruption `interrupt_before=["physician_node"]` permet à LangGraph Studio
    de visualiser l'état AVANT que le médecin n'intervienne.
    """
    logger.info("[Graph] Construction du graphe clinique...")

    builder = StateGraph(ClinicalWorkflowState)

    # ── Ajout des nœuds ──────────────────────────────────────────────────────
    builder.add_node("supervisor",        supervisor_node)
    builder.add_node("diagnostic_agent",  diagnostic_agent_node)
    builder.add_node("physician_node",    physician_review_node)   # Human-in-the-Loop
    builder.add_node("report_agent",      report_agent_node)

    # ── Arêtes fixes ─────────────────────────────────────────────────────────
    builder.add_edge(START,          "supervisor")
    builder.add_edge("report_agent", END)

    # ── Arêtes conditionnelles ────────────────────────────────────────────────
    builder.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "diagnostic_agent": "diagnostic_agent",
            "physician_node":   "physician_node",
            "report_agent":     "report_agent",
            "__end__":          END,
        },
    )

    builder.add_conditional_edges(
        "diagnostic_agent",
        route_after_diagnostic,
        {
            "supervisor": "supervisor",
            END:          END,
        },
    )

    builder.add_conditional_edges(
        "physician_node",
        route_after_physician,
        {
            "report_agent": "report_agent",
            END:            END,
        },
    )

    # ── Compilation avec checkpointer et interruption HITL ───────────────────
    checkpointer = MemorySaver()
    graph = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["physician_node"],  # Human-in-the-Loop obligatoire
    )

    logger.info("[Graph] Graphe compilé avec succès ✓")
    return graph


# ── Singleton du graphe (réutilisé par l'API et LangGraph Studio) ─────────────

_graph_instance = None


def get_graph():
    """
    Retourne l'instance unique du graphe (singleton).
    Cette fonction est référencée dans langgraph.json pour LangGraph Studio.
    """
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = build_clinical_graph()
    return _graph_instance
