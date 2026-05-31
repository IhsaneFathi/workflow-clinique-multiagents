import logging
from datetime import datetime, timezone
from langchain_core.messages import AIMessage
from ..state import ClinicalWorkflowState

logger = logging.getLogger(__name__)


def physician_review_node(state: ClinicalWorkflowState) -> dict:
    logger.info("[PhysicianReview] Entered")
    physician_review = state.get("physician_review")

    if not physician_review or not physician_review.validation:
        logger.info("[PhysicianReview] Waiting for physician input (Human-in-the-Loop)")
        return {
            "next_step": "awaiting_physician",
            "workflow_status": "awaiting_physician",
            "messages": [AIMessage(content="En attente de la revue du medecin.", name="physician_review")],
        }

    if not physician_review.reviewed_at:
        physician_review.reviewed_at = datetime.now(timezone.utc).isoformat()

    logger.info("[PhysicianReview] Review received, routing to report_agent")
    return {
        "physician_review": physician_review,
        "next_step": "report_agent",
        "workflow_status": "generating_report",
        "messages": [AIMessage(content=f"Revue medecin validee : {physician_review.validation}", name="physician_review")],
    }
