import logging
from typing import Literal
from ..state import ClinicalWorkflowState

logger = logging.getLogger(__name__)


def supervisor_node(state: ClinicalWorkflowState) -> dict:
    answers = state.get("answers", [])
    preliminary_summary = state.get("preliminary_summary", "")
    physician_review = state.get("physician_review")
    final_report = state.get("final_report", "")
    current_question_index = state.get("current_question_index", 0)

    if final_report:
        logger.info("[Supervisor] -> END")
        return {"next_step": "END", "workflow_status": "completed"}

    if physician_review and physician_review.validation:
        logger.info("[Supervisor] -> report_agent")
        return {"next_step": "report_agent", "workflow_status": "generating_report"}

    if preliminary_summary and not physician_review:
        logger.info("[Supervisor] -> physician_review")
        return {"next_step": "physician_review", "workflow_status": "awaiting_physician"}

    if len(answers) >= 5 and not preliminary_summary:
        logger.info("[Supervisor] -> diagnostic_agent (generate summary)")
        return {"next_step": "diagnostic_agent", "workflow_status": "generating_summary"}

    logger.info(f"[Supervisor] -> diagnostic_agent (question {current_question_index + 1}/5)")
    return {"next_step": "diagnostic_agent", "workflow_status": "questioning"}


def route_after_supervisor(state: ClinicalWorkflowState) -> Literal["diagnostic_agent", "physician_node", "report_agent", "__end__"]:
    next_step = state.get("next_step", "diagnostic_agent")
    mapping = {
        "diagnostic_agent": "diagnostic_agent",
        "physician_review": "physician_node",
        "report_agent": "report_agent",
        "END": "__end__",
    }
    return mapping.get(next_step, "diagnostic_agent")
