"""
Backend FastAPI — Workflow Clinique Multi-Agents
Gestion d'état manuelle (sans LangGraph interrupt) pour fiabilité maximale.
"""
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Workflow Clinique Multi-Agents", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory store (remplace LangGraph MemorySaver) ─────────────────────────
sessions: dict = {}

CLINICAL_QUESTIONS = [
    "Depuis combien de temps avez-vous ces symptomes ?",
    "Avez-vous de la fievre ? Si oui, a quelle temperature ?",
    "Ressentez-vous une douleur thoracique ou des palpitations ?",
    "Avez-vous des difficultes a respirer ou un essoufflement ?",
    "Prenez-vous actuellement des medicaments ? Si oui, lesquels ?",
]


# ── LLM helper ────────────────────────────────────────────────────────────────
def _get_llm():
    groq_key = os.getenv("GROQ_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if groq_key and groq_key not in ("", "gsk_your-groq-key-here"):
        from langchain_groq import ChatGroq
        model = os.getenv("GROQ_MODEL", "llama3-8b-8192")
        logger.info(f"[LLM] Groq / {model}")
        return ChatGroq(model=model, temperature=0.3, api_key=groq_key)
    if openai_key and openai_key not in ("", "sk-your-openai-key-here"):
        from langchain_openai import ChatOpenAI
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        logger.info(f"[LLM] OpenAI / {model}")
        return ChatOpenAI(model=model, temperature=0.3, api_key=openai_key)
    raise ValueError("Aucune cle LLM valide. Definissez GROQ_API_KEY ou OPENAI_API_KEY dans .env")


# ── MCP helper (synchrone, httpx) ─────────────────────────────────────────────
def _mcp_recommendations(symptoms: str) -> list:
    mcp_url = os.getenv("MCP_SERVER_URL", "http://mcp_server:8001")
    try:
        with httpx.Client(timeout=6.0) as c:
            r = c.post(f"{mcp_url}/tools/call",
                       json={"tool": "general_care_tool",
                             "arguments": {"symptoms_description": symptoms}})
            r.raise_for_status()
            result = r.json().get("result", {})
            if isinstance(result, dict) and "recommandations" in result:
                return result["recommandations"]
    except Exception as e:
        logger.warning(f"[MCP] fallback ({e})")
    return [
        "Repos recommande",
        "Hydratation suffisante (1,5 a 2L/jour)",
        "Surveiller l'evolution des symptomes",
        "Consulter si aggravation",
        "Ne pas s'automedimenter",
    ]


# ── Génération synthèse (appel LLM direct, synchrone) ─────────────────────────
def _generate_summary(session: dict) -> dict:
    """Génère la synthèse clinique. Retourne toujours quelque chose (fallback inclus)."""
    patient_case = session["patient_initial_case"]
    answers = session["answers"]

    qa = ""
    for i, (q, a) in enumerate(zip(CLINICAL_QUESTIONS, answers)):
        qa += f"Q{i+1}: {q}\nR{i+1}: {a}\n\n"

    mcp_recs = _mcp_recommendations(patient_case)
    mcp_text = "\n".join(f"- {r}" for r in mcp_recs)

    try:
        llm = _get_llm()
        from langchain_core.messages import SystemMessage, HumanMessage
        prompt = (
            f"CAS INITIAL:\n{patient_case}\n\n"
            f"QUESTIONNAIRE:\n{qa}\n"
            f"RECOMMANDATIONS:\n{mcp_text}\n\n"
            f"Genere:\n"
            f"1. SYNTHESE CLINIQUE PRELIMINAIRE (non diagnostique, structuree)\n"
            f"2. RECOMMANDATION INTERMEDIAIRE\n\n"
            f"Termine par: Ce systeme ne remplace pas une consultation medicale."
        )
        response = llm.invoke([
            SystemMessage(content="Tu es un agent d'orientation clinique academique. Ne pose jamais de diagnostic definitif."),
            HumanMessage(content=prompt),
        ])
        full = response.content
        logger.info("[Summary] LLM response received")

        if "RECOMMANDATION INTERMEDIAIRE" in full:
            parts = full.split("RECOMMANDATION INTERMEDIAIRE", 1)
            return {
                "preliminary_summary": parts[0].strip(),
                "intermediate_recommendation": "RECOMMANDATION INTERMEDIAIRE" + parts[1].strip(),
                "mcp_recs": mcp_recs,
            }
        return {
            "preliminary_summary": full.strip(),
            "intermediate_recommendation": mcp_text,
            "mcp_recs": mcp_recs,
        }

    except Exception as e:
        logger.error(f"[Summary] LLM error: {e} — template fallback")
        padded = answers + ["Non renseigne"] * (5 - len(answers))
        summary = (
            f"SYNTHESE CLINIQUE PRELIMINAIRE\n"
            f"Patient : {patient_case}\n"
            f"Duree des symptomes : {padded[0]}\n"
            f"Fievre : {padded[1]}\n"
            f"Douleur thoracique : {padded[2]}\n"
            f"Difficultes respiratoires : {padded[3]}\n"
            f"Medicaments : {padded[4]}\n\n"
            f"Ce systeme ne remplace pas une consultation medicale."
        )
        return {
            "preliminary_summary": summary,
            "intermediate_recommendation": f"RECOMMANDATION INTERMEDIAIRE\n{mcp_text}",
            "mcp_recs": mcp_recs,
        }


def _generate_report(session: dict) -> str:
    """Génère le rapport final. Retourne toujours quelque chose."""
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y a %H:%M:%S UTC")
    tid = session["thread_id"]
    patient_case = session["patient_initial_case"]
    answers = session["answers"]
    summary = session.get("preliminary_summary", "")
    reco = session.get("intermediate_recommendation", "")
    pr = session.get("physician_review", {})

    qa = ""
    for i, q in enumerate(CLINICAL_QUESTIONS):
        a = answers[i] if i < len(answers) else "Non renseigne"
        qa += f"Q{i+1}: {q}\nR{i+1}: {a}\n\n"

    pr_text = (
        f"Traitement : {pr.get('treatment','Non specifie')}\n"
        f"Conduite : {pr.get('conduct_to_hold','Non specifie')}\n"
        f"Validation : {pr.get('validation','Non specifie')}"
    ) if pr else "Non disponible"

    try:
        llm = _get_llm()
        from langchain_core.messages import SystemMessage, HumanMessage
        response = llm.invoke([
            SystemMessage(content="Tu generes des rapports cliniques academiques structures."),
            HumanMessage(content=(
                f"Genere un rapport final structure.\nREFERENCE: {tid}\nDATE: {now}\n\n"
                f"CAS INITIAL:\n{patient_case}\n\nQUESTIONNAIRE:\n{qa}\n"
                f"SYNTHESE:\n{summary}\n\nRECOMMANDATION:\n{reco}\n\n"
                f"REVUE MEDECIN:\n{pr_text}\n\n"
                f"Termine par: Ce systeme ne remplace pas une consultation medicale."
            )),
        ])
        logger.info("[Report] LLM report generated")
        return response.content
    except Exception as e:
        logger.error(f"[Report] LLM error: {e} — template")
        return (
            f"===================================================\n"
            f"RAPPORT D'ORIENTATION CLINIQUE SIMULEE\n"
            f"===================================================\n"
            f"DATE : {now}\nREFERENCE : {tid}\n\n"
            f"1. CAS INITIAL\n{patient_case}\n\n"
            f"2. QUESTIONNAIRE\n{qa}\n"
            f"3. SYNTHESE\n{summary}\n\n"
            f"4. RECOMMANDATION\n{reco}\n\n"
            f"5. REVUE MEDICALE\n{pr_text}\n\n"
            f"AVERTISSEMENT: Ce systeme ne remplace pas une consultation medicale.\n"
            f"==================================================="
        )


# ── Schemas ───────────────────────────────────────────────────────────────────
class StartSessionRequest(BaseModel):
    patient_name: Optional[str] = "Patient anonyme"

class StartConsultationRequest(BaseModel):
    thread_id: str
    patient_initial_case: str

class ResumeRequest(BaseModel):
    thread_id: str
    action: str
    patient_answer: Optional[str] = None
    treatment: Optional[str] = None
    conduct_to_hold: Optional[str] = None
    validation: Optional[str] = None


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "healthy", "service": "clinical-workflow-api", "version": "2.0.0"}


@app.post("/sessions/start")
def start_session(req: StartSessionRequest):
    thread_id = str(uuid.uuid4())
    sessions[thread_id] = {
        "thread_id": thread_id,
        "patient_name": req.patient_name,
        "status": "created",
        "workflow_status": "created",
        "patient_initial_case": "",
        "questions": list(CLINICAL_QUESTIONS),
        "answers": [],
        "current_question_index": 0,
        "preliminary_summary": "",
        "intermediate_recommendation": "",
        "mcp_care_recommendations": [],
        "physician_review": None,
        "final_report": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    logger.info(f"[Session] Created {thread_id}")
    return {"thread_id": thread_id, "message": "Session creee.", "created_at": sessions[thread_id]["created_at"]}


@app.post("/consultation/start")
def start_consultation(req: StartConsultationRequest):
    if req.thread_id not in sessions:
        raise HTTPException(status_code=404, detail="Session introuvable. Appelez /sessions/start d'abord.")
    if len(req.patient_initial_case.strip()) < 5:
        raise HTTPException(status_code=400, detail="Le cas patient est trop court.")

    s = sessions[req.thread_id]
    s["patient_initial_case"] = req.patient_initial_case.strip()
    s["workflow_status"] = "questioning"
    s["current_question_index"] = 0
    s["answers"] = []

    q = CLINICAL_QUESTIONS[0]
    logger.info(f"[Consultation] Started {req.thread_id}")
    return {
        "thread_id": req.thread_id,
        "status": "questioning",
        "current_question": f"[Question 1/5] {q}",
        "question_index": 0,
        "message": "Consultation demarree.",
    }


@app.post("/consultation/resume")
def resume_consultation(req: ResumeRequest):
    if req.thread_id not in sessions:
        raise HTTPException(status_code=404, detail="Session introuvable.")

    s = sessions[req.thread_id]

    # ── Patient answer ─────────────────────────────────────────────────────
    if req.action == "answer":
        if not req.patient_answer or not req.patient_answer.strip():
            raise HTTPException(status_code=400, detail="patient_answer requis.")

        s["answers"].append(req.patient_answer.strip())
        new_index = len(s["answers"])
        s["current_question_index"] = new_index
        logger.info(f"[Answer] {req.thread_id} → answer {new_index}/5")

        # Still have questions
        if new_index < 5:
            q = CLINICAL_QUESTIONS[new_index]
            s["workflow_status"] = "questioning"
            return {
                "thread_id": req.thread_id,
                "status": "questioning",
                "current_question": f"[Question {new_index + 1}/5] {q}",
                "question_index": new_index,
                "answers_count": new_index,
                "message": f"Reponse enregistree. Question {new_index + 1}/5.",
            }

        # All 5 answers received — generate summary NOW (synchronous, blocking, reliable)
        logger.info(f"[Summary] Generating for {req.thread_id}...")
        s["workflow_status"] = "generating_summary"

        result = _generate_summary(s)
        s["preliminary_summary"] = result["preliminary_summary"]
        s["intermediate_recommendation"] = result["intermediate_recommendation"]
        s["mcp_care_recommendations"] = result["mcp_recs"]
        s["workflow_status"] = "awaiting_physician"

        logger.info(f"[Summary] Done for {req.thread_id}")
        return {
            "thread_id": req.thread_id,
            "status": "awaiting_physician",
            "message": "5 questions repondues. Synthese generee.",
            "preliminary_summary": s["preliminary_summary"],
            "intermediate_recommendation": s["intermediate_recommendation"],
        }

    # ── Physician review ───────────────────────────────────────────────────
    elif req.action == "physician_review":
        if not req.validation or not req.validation.strip():
            raise HTTPException(status_code=400, detail="'validation' est obligatoire.")

        s["physician_review"] = {
            "treatment": req.treatment or "",
            "conduct_to_hold": req.conduct_to_hold or "",
            "validation": req.validation.strip(),
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
        }
        s["workflow_status"] = "generating_report"
        logger.info(f"[Report] Generating for {req.thread_id}...")

        s["final_report"] = _generate_report(s)
        s["workflow_status"] = "completed"

        logger.info(f"[Report] Done for {req.thread_id}")
        return {
            "thread_id": req.thread_id,
            "status": "completed",
            "message": "Rapport final genere.",
            "final_report": s["final_report"],
        }

    else:
        raise HTTPException(status_code=400, detail=f"Action invalide: '{req.action}'. Utilisez 'answer' ou 'physician_review'.")


@app.get("/consultation/{thread_id}")
def get_consultation(thread_id: str):
    if thread_id not in sessions:
        raise HTTPException(status_code=404, detail="Consultation introuvable.")
    s = sessions[thread_id]
    return {
        "thread_id": thread_id,
        "status": s["workflow_status"],
        "workflow_status": s["workflow_status"],
        "current_question_index": s["current_question_index"],
        "questions": s["questions"],
        "answers": s["answers"],
        "preliminary_summary": s["preliminary_summary"],
        "intermediate_recommendation": s["intermediate_recommendation"],
        "physician_review": s["physician_review"],
        "final_report": s["final_report"],
        "next_step": s["workflow_status"],
    }


@app.get("/consultation/{thread_id}/report")
def get_report(thread_id: str):
    if thread_id not in sessions:
        raise HTTPException(status_code=404, detail="Session introuvable.")
    s = sessions[thread_id]
    if not s["final_report"]:
        raise HTTPException(status_code=404, detail="Rapport non disponible.")
    return {
        "thread_id": thread_id,
        "final_report": s["final_report"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/consultation/{thread_id}/report/pdf")
def download_pdf(thread_id: str):
    if thread_id not in sessions:
        raise HTTPException(status_code=404, detail="Session introuvable.")
    s = sessions[thread_id]
    if not s["final_report"]:
        raise HTTPException(status_code=404, detail="Rapport non disponible.")

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
        import io

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story = []
        for line in s["final_report"].split("\n"):
            clean = line.replace("⚠", "!").replace("✅", "[OK]")
            if clean.strip():
                story.append(Paragraph(clean, styles["Normal"]))
                story.append(Spacer(1, 4))
        doc.build(story)
        pdf = buf.getvalue()
        buf.close()
        return Response(content=pdf, media_type="application/pdf",
                        headers={"Content-Disposition": f"attachment; filename=rapport_{thread_id[:8]}.pdf"})
    except ImportError:
        return Response(content=s["final_report"].encode("utf-8"),
                        media_type="text/plain",
                        headers={"Content-Disposition": f"attachment; filename=rapport_{thread_id[:8]}.txt"})


@app.get("/consultations/history")
def get_history():
    history = [
        {
            "thread_id": s["thread_id"],
            "status": s["workflow_status"],
            "patient_name": s.get("patient_name", ""),
            "patient_case": s["patient_initial_case"][:80],
            "created_at": s.get("created_at", ""),
        }
        for s in sessions.values()
    ]
    return {"consultations": history, "total": len(history)}
