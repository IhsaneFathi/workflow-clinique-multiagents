import logging
import os
from datetime import datetime, timezone
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from ..state import ClinicalWorkflowState
from ..prompts import REPORT_AGENT_SYSTEM_PROMPT
from ..tools.patient_tools import CLINICAL_QUESTIONS

logger = logging.getLogger(__name__)


def _get_llm():
    groq_key = os.getenv("GROQ_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if groq_key:
        from langchain_groq import ChatGroq
        model = os.getenv("GROQ_MODEL", "llama3-8b-8192")
        return ChatGroq(model=model, temperature=0.2, api_key=groq_key)
    if openai_key:
        from langchain_openai import ChatOpenAI
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return ChatOpenAI(model=model, temperature=0.2, api_key=openai_key)
    raise ValueError("No LLM API key found. Set GROQ_API_KEY or OPENAI_API_KEY.")


def report_agent_node(state: ClinicalWorkflowState) -> dict:
    logger.info("[ReportAgent] Generating final report")
    thread_id = state.get("thread_id", "N/A")
    patient_case = state.get("patient_initial_case", "Non specifie")
    answers = state.get("answers", [])
    preliminary_summary = state.get("preliminary_summary", "")
    intermediate_recommendation = state.get("intermediate_recommendation", "")
    physician_review = state.get("physician_review")
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y a %H:%M:%S UTC")

    try:
        final_report = _generate_with_llm(
            thread_id, patient_case, answers, preliminary_summary,
            intermediate_recommendation, physician_review, now
        )
    except Exception as e:
        logger.error(f"[ReportAgent] LLM error: {e} — using template")
        final_report = _generate_template(
            thread_id, patient_case, answers, preliminary_summary,
            intermediate_recommendation, physician_review, now
        )

    logger.info("[ReportAgent] Report generated")
    return {
        "final_report": final_report,
        "next_step": "END",
        "workflow_status": "completed",
        "messages": [AIMessage(content="Rapport final genere.", name="report_agent")],
    }


def _generate_with_llm(thread_id, patient_case, answers, preliminary_summary,
                       intermediate_recommendation, physician_review, timestamp) -> str:
    llm = _get_llm()
    qa = ""
    for i, q in enumerate(CLINICAL_QUESTIONS):
        a = answers[i] if i < len(answers) else "Non renseigne"
        qa += f"Q{i+1}: {q}\nR{i+1}: {a}\n\n"

    pr_section = ""
    if physician_review:
        pr_section = (
            f"Traitement : {physician_review.treatment}\n"
            f"Conduite : {physician_review.conduct_to_hold}\n"
            f"Validation : {physician_review.validation}"
        )

    prompt = (
        f"Genere un rapport final structure.\n\n"
        f"REFERENCE: {thread_id}\nDATE: {timestamp}\n\n"
        f"CAS INITIAL:\n{patient_case}\n\n"
        f"QUESTIONNAIRE:\n{qa}\n"
        f"SYNTHESE PRELIMINAIRE:\n{preliminary_summary}\n\n"
        f"RECOMMANDATION:\n{intermediate_recommendation}\n\n"
        f"REVUE MEDECIN:\n{pr_section}\n\n"
        f"Termine par : Ce systeme ne remplace pas une consultation medicale."
    )
    response = llm.invoke([SystemMessage(content=REPORT_AGENT_SYSTEM_PROMPT), HumanMessage(content=prompt)])
    return response.content


def _generate_template(thread_id, patient_case, answers, preliminary_summary,
                       intermediate_recommendation, physician_review, timestamp) -> str:
    qa = ""
    for i, q in enumerate(CLINICAL_QUESTIONS):
        a = answers[i] if i < len(answers) else "Non renseigne"
        qa += f"\nQ{i+1}: {q}\nR{i+1}: {a}\n"

    pr = "Non disponible"
    if physician_review:
        pr = (
            f"Traitement : {physician_review.treatment or 'Non specifie'}\n"
            f"Conduite : {physician_review.conduct_to_hold or 'Non specifie'}\n"
            f"Validation : {physician_review.validation or 'Non specifie'}"
        )

    return f"""===================================================
RAPPORT D'ORIENTATION CLINIQUE SIMULEE
Systeme academique - Usage educatif uniquement
===================================================
DATE : {timestamp}
REFERENCE : {thread_id}

1. CAS INITIAL
--------------
{patient_case}

2. QUESTIONNAIRE
----------------
{qa}

3. SYNTHESE PRELIMINAIRE
-------------------------
{preliminary_summary}

4. RECOMMANDATION INTERMEDIAIRE
--------------------------------
{intermediate_recommendation}

5. REVUE MEDICALE
-----------------
{pr}

6. AVERTISSEMENT LEGAL
-----------------------
Ce systeme ne remplace pas une consultation medicale.
==================================================="""
