import logging
import os
import httpx
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from ..state import ClinicalWorkflowState
from ..prompts import DIAGNOSTIC_AGENT_SYSTEM_PROMPT
from ..tools.patient_tools import CLINICAL_QUESTIONS

logger = logging.getLogger(__name__)


def _get_llm():
    """Return the right LLM based on env vars. Supports OpenAI and Groq."""
    groq_key = os.getenv("GROQ_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")

    if groq_key:
        from langchain_groq import ChatGroq
        model = os.getenv("GROQ_MODEL", "llama3-8b-8192")
        logger.info(f"[LLM] Using Groq model: {model}")
        return ChatGroq(model=model, temperature=0.3, api_key=groq_key)

    if openai_key:
        from langchain_openai import ChatOpenAI
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        logger.info(f"[LLM] Using OpenAI model: {model}")
        return ChatOpenAI(model=model, temperature=0.3, api_key=openai_key)

    raise ValueError("No LLM API key found. Set GROQ_API_KEY or OPENAI_API_KEY in your .env file.")


def _get_mcp_recommendations_sync(symptoms: str) -> list:
    """Call MCP server synchronously using httpx (no asyncio conflicts)."""
    mcp_url = os.getenv("MCP_SERVER_URL", "http://mcp_server:8001")
    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.post(
                f"{mcp_url}/tools/call",
                json={"tool": "general_care_tool", "arguments": {"symptoms_description": symptoms}},
            )
            resp.raise_for_status()
            result = resp.json().get("result", {})
            if isinstance(result, dict) and "recommandations" in result:
                return result["recommandations"]
    except Exception as e:
        logger.warning(f"[DiagnosticAgent] MCP error (using fallback): {e}")
    return [
        "Repos recommande",
        "Hydratation suffisante (1,5 a 2 litres d'eau par jour)",
        "Surveillance de l'evolution des symptomes",
        "Consultation medicale si aggravation",
        "Ne pas prendre de medicaments sans avis medical",
    ]


def diagnostic_agent_node(state: ClinicalWorkflowState) -> dict:
    answers = state.get("answers", [])
    current_index = state.get("current_question_index", 0)

    logger.info(f"[DiagnosticAgent] index={current_index}, answers={len(answers)}")

    # Phase 1: ask questions one by one
    if current_index < 5 and len(answers) < 5:
        question_text = CLINICAL_QUESTIONS[current_index]
        questions = list(state.get("questions", []))
        if len(questions) <= current_index:
            questions.append(question_text)
        logger.info(f"[DiagnosticAgent] Posing question {current_index + 1}/5")
        return {
            "questions": questions,
            "current_question_index": current_index,
            "next_step": "awaiting_answer",
            "workflow_status": "questioning",
            "messages": [AIMessage(content=f"[Question {current_index + 1}/5] {question_text}", name="diagnostic_agent")],
        }

    # Phase 2: generate summary after 5 answers
    if len(answers) >= 5 and not state.get("preliminary_summary"):
        logger.info("[DiagnosticAgent] Generating clinical summary")
        return _generate_clinical_summary(state)

    # Phase 2b: summary already done
    logger.info("[DiagnosticAgent] Summary already done, routing to physician")
    return {
        "next_step": "physician_review",
        "workflow_status": "awaiting_physician",
    }


def _generate_clinical_summary(state: ClinicalWorkflowState) -> dict:
    patient_case = state.get("patient_initial_case", "Non specifie")
    answers = state.get("answers", [])

    qa_pairs = ""
    for i, (q, a) in enumerate(zip(CLINICAL_QUESTIONS, answers)):
        qa_pairs += f"\nQ{i+1}: {q}\nR{i+1}: {a}\n"

    # Get MCP recommendations synchronously (no asyncio)
    mcp_recs = _get_mcp_recommendations_sync(patient_case)
    mcp_text = "\n".join(f"- {r}" for r in mcp_recs)

    preliminary_summary = ""
    intermediate_recommendation = ""

    try:
        llm = _get_llm()
        prompt = (
            f"Tu es un agent d'orientation clinique academique. Genere une synthese clinique PRELIMINAIRE.\n\n"
            f"CAS INITIAL :\n{patient_case}\n\n"
            f"QUESTIONNAIRE :\n{qa_pairs}\n\n"
            f"RECOMMANDATIONS MCP :\n{mcp_text}\n\n"
            f"Genere :\n"
            f"1. Une SYNTHESE CLINIQUE PRELIMINAIRE structuree (non diagnostique)\n"
            f"2. Une RECOMMANDATION INTERMEDIAIRE PRUDENTE\n\n"
            f"Termine par : Ce systeme ne remplace pas une consultation medicale."
        )
        response = llm.invoke([
            SystemMessage(content=DIAGNOSTIC_AGENT_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        full = response.content
        if "RECOMMANDATION INTERMEDIAIRE" in full:
            parts = full.split("RECOMMANDATION INTERMEDIAIRE", 1)
            preliminary_summary = parts[0].strip()
            intermediate_recommendation = "RECOMMANDATION INTERMEDIAIRE" + parts[1].strip()
        else:
            preliminary_summary = full
            intermediate_recommendation = mcp_text

        logger.info("[DiagnosticAgent] Summary generated successfully via LLM")

    except Exception as e:
        logger.error(f"[DiagnosticAgent] LLM error: {e} — using template fallback")
        padded = answers + ["Non renseigne"] * (5 - len(answers))
        preliminary_summary = (
            f"SYNTHESE CLINIQUE PRELIMINAIRE\n"
            f"Patient : {patient_case}\n"
            f"Duree des symptomes : {padded[0]}\n"
            f"Fievre : {padded[1]}\n"
            f"Douleur thoracique : {padded[2]}\n"
            f"Difficultes respiratoires : {padded[3]}\n"
            f"Medicaments : {padded[4]}\n\n"
            f"Ce systeme ne remplace pas une consultation medicale."
        )
        intermediate_recommendation = f"RECOMMANDATION INTERMEDIAIRE\n{mcp_text}"

    return {
        "preliminary_summary": preliminary_summary,
        "intermediate_recommendation": intermediate_recommendation,
        "mcp_care_recommendations": mcp_recs,
        "next_step": "physician_review",
        "workflow_status": "awaiting_physician",
        "messages": [AIMessage(content=f"Synthese generee.\n\n{preliminary_summary[:200]}...", name="diagnostic_agent")],
    }
