# Workflow Multi-Agents d'Orientation Clinique Simulee


## Avertissement ethique

Ce systeme est un **exercice academique uniquement**.
Il ne constitue pas un dispositif medical et **ne remplace pas une consultation medicale**.
Toutes les orientations produites sont des **recommandations intermediaires simulees**.

---

## Technologies

![Python](https://img.shields.io/badge/Python-3.11-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-teal)
![Streamlit](https://img.shields.io/badge/Streamlit-1.36-red)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)
![Groq](https://img.shields.io/badge/LLM-Groq%20llama3-orange)

---

## Architecture

```
project_medical/
├── backend/
│   ├── app/
│   │   ├── graph.py              ← Graphe LangGraph (LangGraph Studio)
│   │   ├── state.py              ← Etat partage ClinicalWorkflowState
│   │   ├── api.py                ← API FastAPI (toutes les routes)
│   │   ├── nodes/
│   │   │   ├── supervisor.py     ← Orchestrateur du workflow
│   │   │   ├── diagnostic_agent.py ← 5 questions + synthese (LLM + MCP)
│   │   │   ├── physician_review.py ← Human-in-the-Loop medecin
│   │   │   └── report_agent.py   ← Rapport final structure
│   │   └── tools/
│   │       ├── patient_tools.py  ← 5 questions cliniques
│   │       └── mcp_client.py     ← Client MCP
│   ├── langgraph.json            ← Config LangGraph Studio
│   └── requirements.txt
├── mcp_server/
│   └── server.py                 ← Serveur MCP (3 outils)
├── frontend/
│   └── app.py                    ← Interface Streamlit
├── docker-compose.yml
└── README.md
```

---

## Workflow LangGraph

```
START
  ↓
Supervisor
  ↓
DiagnosticAgent
  ├── Tool: ask_patient (boucle 5 questions)
  ├── MCP: general_care_tool (recommandations)
  └── LLM: synthese clinique preliminaire
  ↓
Supervisor
  ↓
PhysicianReview  ← INTERRUPT Human-in-the-Loop
  ↓  (medecin saisit traitement + validation)
Supervisor
  ↓
ReportAgent (rapport final structure)
  ↓
END
```

---

## Installation et lancement

### Prerequis
- Docker & Docker Compose installe
- Fichier `.env` avec votre cle Groq

### Creer le fichier .env

Creez un fichier `.env` a la racine du projet :

```env
GROQ_API_KEY=votre_cle_groq_ici
GROQ_MODEL=llama3-8b-8192
MCP_SERVER_URL=http://mcp_server:8001
SQLITE_DB_PATH=/app/data/clinical_workflow.db
```

> Obtenez une cle gratuite sur https://console.groq.com

### Lancement avec Docker (recommande)

```bash
docker-compose up --build
```

Services disponibles :
- Frontend Streamlit  → http://localhost:8501
- Backend FastAPI     → http://localhost:8000
- API Docs            → http://localhost:8000/docs
- MCP Server          → http://localhost:8001

### Lancement sans Docker

```bash
# Terminal 1 - MCP Server
cd mcp_server
pip install fastapi uvicorn
uvicorn server:app --port 8001 --reload

# Terminal 2 - Backend
cd backend
pip install -r requirements.txt
uvicorn app.api:app --port 8000 --reload

# Terminal 3 - Frontend
cd frontend
pip install streamlit requests
streamlit run app.py
```

### LangGraph Studio

```bash
# Dans Anaconda Prompt
conda activate langgraph_studio
cd backend
langgraph dev
# Ouvre automatiquement LangGraph Studio dans le navigateur
# URL : https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

---

## API FastAPI — Endpoints

| Methode | Route | Description |
|---------|-------|-------------|
| GET | `/health` | Sante du service |
| POST | `/sessions/start` | Creer une session |
| POST | `/consultation/start` | Demarrer une consultation |
| POST | `/consultation/resume` | Repondre (patient ou medecin) |
| GET | `/consultation/{id}` | Etat courant |
| GET | `/consultation/{id}/report` | Rapport final JSON |
| GET | `/consultation/{id}/report/pdf` | Rapport final PDF |
| GET | `/consultations/history` | Historique des consultations |

---

## Integration MCP

Le serveur MCP expose 3 outils :

| Outil | Description |
|-------|-------------|
| `general_care_tool` | Recommandations generales (repos, hydratation, surveillance) |
| `get_urgency_indicators` | Signes d'alarme necessitant consultation urgente |
| `get_monitoring_checklist` | Checklist de surveillance des symptomes |

---

## Jeux de tests — LangGraph Studio

**Cas 1 — Syndrome respiratoire simple**
```
Cas initial : "Toux seche, leger mal de gorge depuis 2 jours, pas de fievre"
Reponses : ["2 jours", "Non", "Non", "Legere gene", "Aucun"]
```

**Cas 2 — Cas avec red flags**
```
Cas initial : "Douleur thoracique intense, difficultes a respirer depuis 1h"
Reponses : ["1 heure", "38.9C", "Oui, douleur forte", "Oui, essoufflement", "Aspirine"]
```

**Cas 3 — Cas benin**
```
Cas initial : "Legere fatigue et nez qui coule, rhume probable"
Reponses : ["4 jours", "Non", "Non", "Non", "Aucun"]
```

Pour chaque cas, verifier :
- 5 questions posees successivement
- Synthese clinique preliminaire generee
- Recommandation intermediaire (via MCP)
- Interruption avant physician_node (Human-in-the-Loop)
- Rapport final apres validation medecin

---

## Conformite cahier des charges

| Exigence | Statut |
|----------|--------|
| LangGraph + Supervisor | OK |
| DiagnosticAgent (5 questions + synthese) | OK |
| PhysicianReview (Human-in-the-Loop) | OK |
| ReportAgent (rapport final) | OK |
| Outil via MCP | OK |
| API FastAPI | OK |
| Frontend Streamlit | OK |
| LangGraph Studio | OK |
| Docker / docker-compose (bonus) | OK |
| Export PDF (bonus) | OK |
| Historique consultations (bonus) | OK |

---

## Stack technique

- **LangGraph** — workflow multi-agents avec etat partage et Human-in-the-Loop
- **LangChain + Groq** — integration LLM (llama3-8b-8192)
- **FastAPI** — API REST
- **MCP** — serveur d'outils externe
- **Streamlit** — interface utilisateur professionnelle
- **Docker** — containerisation complete
- **ReportLab** — export PDF

---

## Captures

<img width="947" height="411" alt="Capture45" src="https://github.com/user-attachments/assets/efc40be4-ca1e-43b9-830b-49183992219c" />

<img width="1600" height="738" alt="image" src="https://github.com/user-attachments/assets/cab9ccfe-fac7-4132-bc03-18f1406e0a98" />

<img width="1600" height="736" alt="image" src="https://github.com/user-attachments/assets/2a852797-650c-4c4d-b28f-d1cbbc3fda5b" />

<img width="1600" height="746" alt="image" src="https://github.com/user-attachments/assets/0a5ee17b-8747-4c7d-b45f-b46c790f57c4" />
