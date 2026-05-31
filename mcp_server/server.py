import logging
from datetime import datetime, timezone
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP Server", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class ToolCallRequest(BaseModel):
    tool: str
    arguments: dict = {}


class ToolCallResponse(BaseModel):
    tool: str
    result: Any
    called_at: str


def _general_care_tool(symptoms_description: str = "") -> dict:
    return {
        "recommandations": [
            "Repos : Accordez-vous un repos suffisant, evitez les efforts physiques intenses.",
            "Hydratation : Buvez regulierement (1,5 a 2 litres d'eau par jour minimum).",
            "Surveillance : Notez l'evolution de vos symptomes.",
            "Consultation medicale : Consultez un medecin si vos symptomes persistent ou s'aggravent.",
            "Medicaments : Ne prenez aucun traitement sans avis medical prealable.",
            "Urgence : En cas de symptomes graves, appelez le 15 ou le 112.",
        ],
        "avertissement": "Ce systeme ne remplace pas une consultation medicale.",
        "contexte_symptomes": symptoms_description or "Non precise",
        "source": "mcp_server",
    }


TOOLS_REGISTRY = {
    "general_care_tool": lambda args: _general_care_tool(args.get("symptoms_description", "")),
    "get_urgency_indicators": lambda args: {
        "signes_alarme": ["Douleur thoracique intense", "Difficultes respiratoires severes", "Perte de conscience"],
        "action_urgente": "Appelez le 15 (SAMU) ou le 112.",
        "source": "mcp_server",
    },
    "get_monitoring_checklist": lambda args: {
        "elements": ["Temperature toutes les 6h", "Intensite douleur toutes les 4h", "Nouveaux symptomes en continu"],
        "source": "mcp_server",
    },
}


@app.get("/tools")
async def list_tools():
    return {"tools": [{"name": k} for k in TOOLS_REGISTRY], "count": len(TOOLS_REGISTRY)}


@app.post("/tools/call", response_model=ToolCallResponse)
async def call_tool(request: ToolCallRequest):
    if request.tool not in TOOLS_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Outil '{request.tool}' non trouve.")
    try:
        result = TOOLS_REGISTRY[request.tool](request.arguments)
        return ToolCallResponse(
            tool=request.tool,
            result=result,
            called_at=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "clinical-mcp-server"}
