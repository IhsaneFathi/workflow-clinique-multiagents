"""
ClinicalFlow — Interface professionnelle SaaS médical
Workflow d'Orientation Clinique Simulée
"""

import os
import time
from datetime import datetime
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://backend:8000")

st.set_page_config(
    page_title="ClinicalFlow — Orientation Clinique",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Design System ────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 14px;
  color: #1a2332;
  background: #f0f2f5;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] > div { padding-top: 0 !important; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
  background: #0f1923 !important;
  border-right: 1px solid #1e2d3d;
}

section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stCaption { color: #8a9bb0 !important; }

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #ffffff !important; }

/* ── Sidebar logo zone ── */
.sidebar-logo {
  padding: 24px 20px 20px;
  border-bottom: 1px solid #1e2d3d;
  margin-bottom: 8px;
}
.sidebar-logo-text {
  font-size: 18px; font-weight: 700; color: #ffffff;
  letter-spacing: -0.3px; display: flex; align-items: center; gap: 8px;
}
.sidebar-logo-sub {
  font-size: 11px; color: #4a6278; margin-top: 3px; font-weight: 400;
}

/* ── Sidebar nav ── */
.nav-section-title {
  font-size: 10px; font-weight: 600; color: #4a6278;
  text-transform: uppercase; letter-spacing: 1px;
  padding: 16px 20px 6px;
}
.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 20px; font-size: 13px; font-weight: 500;
  color: #8a9bb0; cursor: pointer; border-left: 3px solid transparent;
  transition: all 0.15s;
}
.nav-item.active {
  color: #ffffff; background: rgba(37,99,235,0.12);
  border-left-color: #2563eb;
}
.nav-item.done { color: #16a34a; }
.nav-item.locked { color: #374151; opacity: 0.5; }
.nav-icon { width: 16px; text-align: center; font-size: 13px; }
.nav-step-num {
  margin-left: auto; font-size: 10px; font-weight: 600;
  background: rgba(37,99,235,0.2); color: #60a5fa;
  padding: 2px 7px; border-radius: 10px;
}
.nav-step-done {
  margin-left: auto; font-size: 10px; color: #16a34a;
}

/* ── Sidebar session card ── */
.sidebar-session {
  margin: 12px 16px;
  background: #1a2535;
  border: 1px solid #1e2d3d;
  border-radius: 8px;
  padding: 12px 14px;
}
.sidebar-session-label { font-size: 10px; color: #4a6278; text-transform: uppercase; letter-spacing: 0.8px; }
.sidebar-session-id { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #60a5fa; margin-top: 4px; word-break: break-all; }

.sidebar-status-dot {
  width: 7px; height: 7px; border-radius: 50%;
  display: inline-block; margin-right: 6px;
}
.dot-green { background: #22c55e; box-shadow: 0 0 6px #22c55e66; }
.dot-orange { background: #f59e0b; }
.dot-gray { background: #4b5563; }

/* ── Sidebar history ── */
.history-item {
  padding: 8px 20px; font-size: 12px; color: #6b7280;
  border-bottom: 1px solid #111827;
  display: flex; align-items: center; gap: 8px;
}
.history-id { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #374151; }
.history-status { font-size: 10px; margin-left: auto; }

/* ── Main content wrapper ── */
.main-wrap { padding: 0; background: #f0f2f5; min-height: 100vh; }

/* ── Top bar ── */
.topbar {
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  padding: 0 32px;
  height: 56px;
  display: flex; align-items: center;
  justify-content: space-between;
  position: sticky; top: 0; z-index: 100;
}
.topbar-title { font-size: 15px; font-weight: 600; color: #1a2332; }
.topbar-sub { font-size: 12px; color: #64748b; margin-top: 1px; }
.topbar-right { display: flex; align-items: center; gap: 16px; }
.topbar-badge {
  font-size: 11px; font-weight: 600; padding: 4px 10px;
  border-radius: 20px; display: inline-flex; align-items: center; gap: 5px;
}
.badge-info { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }
.badge-warning { background: #fff7ed; color: #c2410c; border: 1px solid #fed7aa; }
.badge-success { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }

/* ── Workflow progress bar ── */
.workflow-bar {
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  padding: 0 32px;
}
.wf-steps {
  display: flex; align-items: stretch;
}
.wf-step {
  flex: 1; display: flex; align-items: center; gap: 10px;
  padding: 14px 0; position: relative;
  font-size: 12px; font-weight: 500; color: #94a3b8;
}
.wf-step:not(:last-child)::after {
  content: ''; position: absolute; right: 0; top: 50%;
  transform: translateY(-50%);
  width: 1px; height: 24px; background: #e2e8f0;
}
.wf-step.active { color: #2563eb; }
.wf-step.done { color: #16a34a; }
.wf-step-circle {
  width: 26px; height: 26px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; flex-shrink: 0;
  background: #f1f5f9; color: #94a3b8; border: 2px solid #e2e8f0;
}
.wf-step.active .wf-step-circle {
  background: #2563eb; color: #fff; border-color: #2563eb;
}
.wf-step.done .wf-step-circle {
  background: #16a34a; color: #fff; border-color: #16a34a;
}
.wf-step-label { line-height: 1.2; }
.wf-step-label small { display: block; font-size: 10px; font-weight: 400; color: #cbd5e1; margin-top: 1px; }
.wf-step.active .wf-step-label small { color: #93c5fd; }
.wf-step.done .wf-step-label small { color: #86efac; }

/* ── Page content area ── */
.page-content { padding: 28px 32px; }

/* ── Section header ── */
.section-header { margin-bottom: 24px; }
.section-title { font-size: 20px; font-weight: 700; color: #0f172a; letter-spacing: -0.3px; }
.section-sub { font-size: 13px; color: #64748b; margin-top: 4px; }

/* ── Cards ── */
.card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 24px;
  margin-bottom: 16px;
}
.card-title {
  font-size: 13px; font-weight: 600; color: #374151;
  text-transform: uppercase; letter-spacing: 0.6px;
  margin-bottom: 16px; display: flex; align-items: center; gap: 8px;
}
.card-title-icon { color: #2563eb; }

/* ── Form elements ── */
.stTextArea textarea, .stTextInput input {
  border: 1px solid #d1d5db !important;
  border-radius: 6px !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 13px !important;
  color: #1a2332 !important;
  background: #ffffff !important;
  padding: 10px 12px !important;
  transition: border-color 0.15s !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
  border-color: #2563eb !important;
  box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important;
}
label[data-testid="stWidgetLabel"] {
  font-size: 13px !important;
  font-weight: 500 !important;
  color: #374151 !important;
}

/* ── Primary button ── */
.stButton > button[kind="primary"] {
  background: #2563eb !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: 6px !important;
  font-weight: 600 !important;
  font-size: 13px !important;
  padding: 10px 20px !important;
  letter-spacing: 0.1px !important;
  transition: background 0.15s !important;
}
.stButton > button[kind="primary"]:hover {
  background: #1d4ed8 !important;
}
.stButton > button {
  border-radius: 6px !important;
  font-weight: 500 !important;
  font-size: 13px !important;
  border: 1px solid #e2e8f0 !important;
  color: #374151 !important;
}

/* ── Q&A items ── */
.qa-item { margin-bottom: 12px; }
.qa-question {
  background: #f8fafc; border: 1px solid #e2e8f0;
  border-radius: 8px 8px 0 0; padding: 12px 16px;
  font-size: 13px; font-weight: 500; color: #1e40af;
  display: flex; align-items: flex-start; gap: 10px;
}
.qa-number {
  background: #2563eb; color: #fff;
  font-size: 10px; font-weight: 700;
  width: 20px; height: 20px; border-radius: 4px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; margin-top: 1px;
}
.qa-answer {
  background: #f0fdf4; border: 1px solid #bbf7d0; border-top: none;
  border-radius: 0 0 8px 8px; padding: 10px 16px 10px 46px;
  font-size: 13px; color: #166534;
}

/* ── Current question card ── */
.current-q-card {
  background: #eff6ff; border: 1px solid #bfdbfe;
  border-left: 4px solid #2563eb;
  border-radius: 8px; padding: 16px 20px;
  margin: 20px 0 16px;
}
.current-q-label {
  font-size: 10px; font-weight: 600; color: #2563eb;
  text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px;
}
.current-q-text { font-size: 14px; font-weight: 500; color: #1e3a8a; }

/* ── Progress tracker ── */
.progress-tracker {
  background: #ffffff; border: 1px solid #e2e8f0;
  border-radius: 10px; padding: 16px 20px; margin-bottom: 20px;
  display: flex; align-items: center; gap: 16px;
}
.progress-label { font-size: 12px; font-weight: 600; color: #374151; min-width: 120px; }
.progress-bar-bg { flex: 1; height: 6px; background: #f1f5f9; border-radius: 3px; overflow: hidden; }
.progress-bar-fill { height: 100%; background: #2563eb; border-radius: 3px; transition: width 0.4s ease; }
.progress-count { font-size: 12px; font-weight: 700; color: #2563eb; min-width: 40px; text-align: right; }

/* ── Summary panels ── */
.summary-panel {
  background: #ffffff; border: 1px solid #e2e8f0;
  border-radius: 10px; overflow: hidden; height: 100%;
}
.summary-panel-header {
  background: #f8fafc; border-bottom: 1px solid #e2e8f0;
  padding: 12px 18px;
  font-size: 12px; font-weight: 600; color: #374151;
  display: flex; align-items: center; gap: 8px;
  text-transform: uppercase; letter-spacing: 0.5px;
}
.summary-panel-body {
  padding: 18px; white-space: pre-wrap;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px; line-height: 1.7; color: #374151;
  max-height: 340px; overflow-y: auto;
}

/* ── Physician form ── */
.physician-form-section {
  background: #ffffff; border: 1px solid #e2e8f0;
  border-radius: 10px; padding: 24px; margin-top: 20px;
}
.form-field-label {
  font-size: 12px; font-weight: 600; color: #374151;
  text-transform: uppercase; letter-spacing: 0.5px;
  margin-bottom: 6px;
}
.required-badge {
  display: inline-block; background: #fee2e2; color: #dc2626;
  font-size: 9px; font-weight: 700; padding: 1px 5px;
  border-radius: 3px; margin-left: 6px; vertical-align: middle;
}

/* ── Report ── */
.report-container {
  background: #ffffff; border: 1px solid #e2e8f0;
  border-radius: 10px; overflow: hidden;
}
.report-header {
  background: #0f1923; padding: 20px 28px;
  display: flex; align-items: center; justify-content: space-between;
}
.report-header-title { font-size: 15px; font-weight: 700; color: #ffffff; }
.report-header-sub { font-size: 11px; color: #4a6278; margin-top: 3px; }
.report-header-badge {
  background: rgba(34,197,94,0.15); color: #22c55e;
  border: 1px solid rgba(34,197,94,0.3);
  font-size: 11px; font-weight: 600; padding: 5px 12px; border-radius: 20px;
}
.report-body {
  padding: 28px; white-space: pre-wrap;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px; line-height: 1.8; color: #1a2332;
  max-height: 520px; overflow-y: auto;
}

/* ── Alerts ── */
.alert {
  border-radius: 8px; padding: 12px 16px;
  font-size: 13px; margin: 12px 0;
  display: flex; align-items: flex-start; gap: 10px;
}
.alert-warning { background: #fff7ed; border: 1px solid #fed7aa; color: #92400e; }
.alert-info    { background: #eff6ff; border: 1px solid #bfdbfe; color: #1e40af; }
.alert-success { background: #f0fdf4; border: 1px solid #bbf7d0; color: #14532d; }
.alert-error   { background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; }
.alert-icon { font-size: 15px; flex-shrink: 0; margin-top: 1px; }

/* ── Examples ── */
.example-card {
  background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;
  padding: 12px 14px; margin-bottom: 8px; cursor: pointer;
  font-size: 12px; color: #374151; line-height: 1.5;
  transition: border-color 0.15s, background 0.15s;
}
.example-card:hover { border-color: #2563eb; background: #eff6ff; color: #1e40af; }
.example-tag {
  display: inline-block; font-size: 10px; font-weight: 600;
  padding: 2px 6px; border-radius: 4px; margin-bottom: 5px;
}
.tag-respiratory { background: #eff6ff; color: #2563eb; }
.tag-abdominal   { background: #fef3c7; color: #92400e; }
.tag-neurological { background: #f5f3ff; color: #5b21b6; }

/* ── Info grid ── */
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px; }
.info-cell {
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;
  padding: 14px 16px;
}
.info-cell-label { font-size: 10px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; }
.info-cell-value { font-size: 14px; font-weight: 600; color: #1a2332; margin-top: 4px; }

/* ── Divider ── */
.divider { border: none; border-top: 1px solid #e2e8f0; margin: 20px 0; }

/* ── Download buttons ── */
.stDownloadButton > button {
  border-radius: 6px !important;
  font-weight: 500 !important;
  font-size: 13px !important;
  border: 1px solid #e2e8f0 !important;
  background: #ffffff !important;
  color: #374151 !important;
}

/* ── Streamlit alerts override ── */
.stAlert { border-radius: 8px !important; font-size: 13px !important; }

/* ── Spinner ── */
.stSpinner { color: #2563eb !important; }
</style>
""", unsafe_allow_html=True)

# ─── API Helpers ──────────────────────────────────────────────────────────────

def api_post(endpoint: str, payload: dict, timeout: int = 180):
    try:
        r = requests.post(f"{API_BASE}{endpoint}", json=payload, timeout=timeout)
        if r.status_code >= 400:
            try:
                detail = r.json().get("detail", r.text)
            except Exception:
                detail = r.text
            st.error(f"Erreur API {r.status_code} : {detail}")
            return None
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Impossible de joindre le backend ({API_BASE}). Docker est-il lancé ?")
        return None
    except requests.exceptions.Timeout:
        st.error("Délai dépassé. Vérifiez votre clé API Groq dans le fichier .env")
        return None
    except Exception as e:
        st.error(f"Erreur : {e}")
        return None

def api_get(endpoint: str, timeout: int = 30):
    try:
        r = requests.get(f"{API_BASE}{endpoint}", timeout=timeout)
        return r.json() if r.status_code < 400 else None
    except Exception:
        return None

def get_pdf_bytes(thread_id: str):
    try:
        r = requests.get(f"{API_BASE}/consultation/{thread_id}/report/pdf", timeout=30)
        return r.content if r.status_code == 200 else None
    except Exception:
        return None

def backend_ok() -> bool:
    try:
        r = requests.get(f"{API_BASE}/health", timeout=4)
        return r.status_code == 200
    except Exception:
        return False

# ─── Session State ────────────────────────────────────────────────────────────

DEFAULTS = {
    "screen": "home",
    "thread_id": None,
    "patient_case": "",
    "patient_name": "",
    "pending_case": "",
    "current_question": None,
    "question_index": 0,
    "questions_asked": [],
    "answers_given": [],
    "preliminary_summary": "",
    "intermediate_recommendation": "",
    "final_report": "",
    "workflow_status": "",
    "started_at": None,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── Helpers UI ───────────────────────────────────────────────────────────────

STEPS = [
    ("home",       "Informations patient",   "Saisie du cas",         "person"),
    ("questioning","Questionnaire clinique",  "5 questions",           "list"),
    ("physician",  "Validation médicale",    "Human-in-the-Loop",     "stethoscope"),
    ("report",     "Rapport final",          "Génération du rapport", "file"),
]

SCREEN_ORDER = ["home", "questioning", "physician", "report"]

def screen_index(s):
    return SCREEN_ORDER.index(s) if s in SCREEN_ORDER else 0

def wf_bar():
    cur = screen_index(st.session_state.screen)
    icons = ["①","②","③","④"]
    subtitles = ["Cas patient", "5 questions", "Revue médecin", "Rapport"]
    labels = ["Informations patient", "Questionnaire", "Validation médicale", "Rapport final"]
    html = "<div class='workflow-bar'><div class='wf-steps'>"
    for i, (label, sub, icon) in enumerate(zip(labels, subtitles, icons)):
        cls = "active" if i == cur else ("done" if i < cur else "")
        circle = "✓" if i < cur else str(i+1)
        html += f"""<div class='wf-step {cls}'>
          <div class='wf-step-circle'>{circle}</div>
          <div class='wf-step-label'>{label}<small>{sub}</small></div>
        </div>"""
    html += "</div></div>"
    st.markdown(html, unsafe_allow_html=True)

def topbar(title, subtitle, status=None, status_type="info"):
    status_html = ""
    if status:
        status_html = f"<span class='topbar-badge badge-{status_type}'>{status}</span>"
    st.markdown(f"""
<div class='topbar'>
  <div>
    <div class='topbar-title'>⚕️ ClinicalFlow &nbsp;/&nbsp; {title}</div>
    <div class='topbar-sub'>{subtitle}</div>
  </div>
  <div class='topbar-right'>{status_html}</div>
</div>""", unsafe_allow_html=True)

def alert(msg, kind="info"):
    icons = {"info": "ℹ️", "warning": "⚠️", "success": "✅", "error": "❌"}
    st.markdown(f"""<div class='alert alert-{kind}'>
      <span class='alert-icon'>{icons.get(kind,'ℹ️')}</span>
      <span>{msg}</span>
    </div>""", unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
<div class='sidebar-logo'>
  <div class='sidebar-logo-text'>⚕️ ClinicalFlow</div>
  <div class='sidebar-logo-sub'>Système d'orientation clinique simulée</div>
</div>""", unsafe_allow_html=True)

    # Workflow nav
    cur_idx = screen_index(st.session_state.screen)
    st.markdown("<div class='nav-section-title'>Workflow</div>", unsafe_allow_html=True)
    nav_icons = ["👤", "💬", "🩺", "📄"]
    nav_labels = ["Informations patient", "Questionnaire", "Validation médicale", "Rapport final"]
    nav_subs = ["Cas initial", "5 questions", "Human-in-the-Loop", "Génération"]
    for i, (icon, label) in enumerate(zip(nav_icons, nav_labels)):
        screen = SCREEN_ORDER[i]
        if i == cur_idx:
            cls = "active"
            badge = f"<span class='nav-step-num'>En cours</span>"
        elif i < cur_idx:
            cls = "done"
            badge = "<span class='nav-step-done'>✓</span>"
        else:
            cls = "locked"
            badge = ""
        st.markdown(f"""<div class='nav-item {cls}'>
          <span class='nav-icon'>{icon}</span> {label} {badge}
        </div>""", unsafe_allow_html=True)

    # Session active
    if st.session_state.thread_id:
        st.markdown(f"""
<div class='sidebar-session'>
  <div class='sidebar-session-label'>Session active</div>
  <div class='sidebar-session-id'>{st.session_state.thread_id[:20]}…</div>
  <div style='margin-top:8px;font-size:11px;color:#4a6278'>
    <span class='sidebar-status-dot dot-green'></span>En cours
    &nbsp;·&nbsp;
    Q {len(st.session_state.answers_given)}/5
  </div>
</div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Backend status
    ok = backend_ok()
    dot = "dot-green" if ok else "dot-gray"
    status_text = "Backend connecté" if ok else "Backend hors ligne"
    st.markdown(f"<div style='padding:0 20px 12px;font-size:12px;color:#8a9bb0'><span class='sidebar-status-dot {dot}'></span>{status_text}</div>", unsafe_allow_html=True)

    # Nouvelle consultation
    st.markdown("<div style='padding:0 16px 8px'>", unsafe_allow_html=True)
    if st.button("＋ Nouvelle consultation", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # Historique
    st.markdown("<div class='nav-section-title'>Historique récent</div>", unsafe_allow_html=True)
    hist = api_get("/consultations/history")
    if hist and hist.get("consultations"):
        for c in hist["consultations"][-6:]:
            sid = c["thread_id"][:8]
            ws = c.get("status", "?")
            dot_c = "dot-green" if ws == "completed" else "dot-orange"
            st.markdown(f"""<div class='history-item'>
              <span class='sidebar-status-dot {dot_c}'></span>
              <span class='history-id'>{sid}…</span>
              <span class='history-status'>{ws}</span>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("<div class='history-item'>Aucune consultation</div>", unsafe_allow_html=True)

    # Legal
    st.markdown("""
<div style='padding:16px 20px;font-size:11px;color:#2d3f52;border-top:1px solid #1e2d3d;margin-top:auto'>
  ⚠️ Système académique. Ne remplace pas une consultation médicale réelle.
</div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════
# ÉCRAN 1 — Informations patient
# ════════════════════════════════════════════════════════════════════════

if st.session_state.screen == "home":
    topbar("Nouvelle consultation", "Étape 1 sur 4 — Saisie des informations patient")
    wf_bar()

    st.markdown("<div class='page-content'>", unsafe_allow_html=True)

    alert("Ce système est un outil académique d'aide à l'orientation clinique. Il ne produit aucun diagnostic médical définitif.", "info")

    col_main, col_side = st.columns([3, 1], gap="large")

    with col_main:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'><span class='card-title-icon'>👤</span> Description clinique du patient</div>", unsafe_allow_html=True)

        patient_name = st.text_input(
            "Identifiant ou nom du patient",
            value=st.session_state.patient_name,
            placeholder="Ex : Patient A, Jean D., Dossier #2024-001",
        )

        patient_case = st.text_area(
            "Motif de consultation et symptômes *",
            value=st.session_state.pending_case,
            placeholder="Décrivez les symptômes principaux, leur durée, le contexte clinique et tout antécédent pertinent…",
            height=160,
        )

        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Démarrer la consultation →", type="primary"):
            case_to_use = patient_case.strip() or st.session_state.pending_case.strip()
            if len(case_to_use) < 10:
                alert("Veuillez décrire le motif de consultation (minimum 10 caractères).", "warning")
            else:
                with st.spinner("Initialisation du workflow clinique…"):
                    session_resp = api_post("/sessions/start", {"patient_name": patient_name or "Anonyme"})
                    if not session_resp:
                        st.stop()
                    thread_id = session_resp["thread_id"]
                    consult_resp = api_post("/consultation/start", {
                        "thread_id": thread_id,
                        "patient_initial_case": case_to_use,
                    })
                    if not consult_resp:
                        st.stop()

                    st.session_state.thread_id = thread_id
                    st.session_state.patient_case = case_to_use
                    st.session_state.patient_name = patient_name or "Anonyme"
                    st.session_state.pending_case = ""
                    st.session_state.current_question = consult_resp.get("current_question", "")
                    st.session_state.question_index = consult_resp.get("question_index", 0)
                    st.session_state.questions_asked = []
                    st.session_state.answers_given = []
                    st.session_state.started_at = datetime.now().strftime("%d/%m/%Y %H:%M")
                    st.session_state.screen = "questioning"
                    st.rerun()

    with col_side:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>Cas cliniques types</div>", unsafe_allow_html=True)

        examples = [
            ("Syndrome respiratoire", "tag-respiratory",
             "Patient de 45 ans, fièvre 38.8°C depuis 2 jours, toux sèche persistante et fatigue intense."),
            ("Douleur abdominale", "tag-abdominal",
             "Femme de 30 ans, douleur abdominale droite depuis 24h, nausées, sans fièvre."),
            ("Céphalées avec red flags", "tag-neurological",
             "Homme de 60 ans, céphalées intenses à début brutal, photophobie, légère raideur de la nuque."),
        ]

        for tag, tag_cls, ex in examples:
            st.markdown(f"""<div class='example-card'>
              <div><span class='example-tag {tag_cls}'>{tag}</span></div>
              {ex}
            </div>""", unsafe_allow_html=True)
            if st.button(f"Utiliser →", key=f"ex_{ex[:12]}"):
                st.session_state.pending_case = ex
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        # Info workflow
        st.markdown("""<div class='card' style='margin-top:0'>
          <div class='card-title'>Workflow</div>
          <div style='font-size:12px;color:#64748b;line-height:2'>
            <div>① Saisie du cas patient</div>
            <div>② 5 questions cliniques</div>
            <div>③ Synthèse préliminaire</div>
            <div>④ Validation médecin</div>
            <div>⑤ Rapport structuré</div>
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════
# ÉCRAN 2 — Questionnaire clinique
# ════════════════════════════════════════════════════════════════════════

elif st.session_state.screen == "questioning":
    topbar("Questionnaire clinique", "Étape 2 sur 4 — Collecte des informations patient",
           f"Q {len(st.session_state.answers_given) + 1}/5", "info")
    wf_bar()

    st.markdown("<div class='page-content'>", unsafe_allow_html=True)

    answered = len(st.session_state.answers_given)
    pct = int((answered / 5) * 100)

    col_left, col_right = st.columns([3, 1], gap="large")

    with col_left:
        # Progress bar
        st.markdown(f"""<div class='progress-tracker'>
          <div class='progress-label'>Progression</div>
          <div class='progress-bar-bg'>
            <div class='progress-bar-fill' style='width:{pct}%'></div>
          </div>
          <div class='progress-count'>{answered}/5</div>
        </div>""", unsafe_allow_html=True)

        # Q&A history
        if st.session_state.questions_asked:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<div class='card-title'>Réponses enregistrées</div>", unsafe_allow_html=True)
            for i, (q, a) in enumerate(zip(st.session_state.questions_asked, st.session_state.answers_given)):
                st.markdown(f"""<div class='qa-item'>
                  <div class='qa-question'>
                    <div class='qa-number'>{i+1}</div>
                    <div>{q}</div>
                  </div>
                  <div class='qa-answer'>{a}</div>
                </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Current question
        if answered < 5:
            current_q = st.session_state.current_question
            if not current_q:
                state_resp = api_get(f"/consultation/{st.session_state.thread_id}")
                if state_resp and state_resp.get("workflow_status") == "awaiting_physician":
                    st.session_state.preliminary_summary = state_resp.get("preliminary_summary", "")
                    st.session_state.intermediate_recommendation = state_resp.get("intermediate_recommendation", "")
                    st.session_state.screen = "physician"
                    st.rerun()

            if current_q:
                display_q = current_q.split("]", 1)[-1].strip() if "]" in current_q else current_q

                st.markdown(f"""<div class='current-q-card'>
                  <div class='current-q-label'>Question {answered + 1} sur 5</div>
                  <div class='current-q-text'>{display_q}</div>
                </div>""", unsafe_allow_html=True)

                answer = st.text_area(
                    "Réponse du patient",
                    placeholder="Saisissez la réponse ici…",
                    height=90,
                    key=f"ans_{answered}",
                )

                btn_label = "Générer la synthèse →" if answered == 4 else "Réponse suivante →"
                if st.button(btn_label, type="primary"):
                    if not answer or not answer.strip():
                        alert("Veuillez saisir une réponse avant de continuer.", "warning")
                    else:
                        spinner_msg = "Génération de la synthèse clinique par l'IA…" if answered == 4 else "Enregistrement…"
                        with st.spinner(spinner_msg):
                            resp = api_post("/consultation/resume", {
                                "thread_id": st.session_state.thread_id,
                                "action": "answer",
                                "patient_answer": answer.strip(),
                            }, timeout=180)

                        if resp is None:
                            alert("Erreur lors de l'envoi. Consultez les logs Docker.", "error")
                            st.stop()

                        st.session_state.questions_asked.append(display_q)
                        st.session_state.answers_given.append(answer.strip())
                        status = resp.get("status", "")

                        if status == "awaiting_physician":
                            st.session_state.preliminary_summary = resp.get("preliminary_summary", "")
                            st.session_state.intermediate_recommendation = resp.get("intermediate_recommendation", "")
                            if not st.session_state.preliminary_summary:
                                sr = api_get(f"/consultation/{st.session_state.thread_id}")
                                if sr:
                                    st.session_state.preliminary_summary = sr.get("preliminary_summary", "")
                                    st.session_state.intermediate_recommendation = sr.get("intermediate_recommendation", "")
                            st.session_state.screen = "physician"
                            st.rerun()
                        else:
                            st.session_state.current_question = resp.get("current_question", "")
                            st.session_state.question_index = resp.get("question_index", answered + 1)
                            st.rerun()
            else:
                alert("Chargement de la question…", "info")
                if st.button("Rafraîchir"):
                    st.rerun()

    with col_right:
        # Patient recap
        st.markdown(f"""<div class='card'>
          <div class='card-title'>Dossier patient</div>
          <div style='font-size:12px;color:#374151;line-height:1.7'>
            <div style='font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px'>Patient</div>
            <div style='font-weight:600;margin-bottom:12px'>{st.session_state.patient_name or "Anonyme"}</div>
            <div style='font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px'>Motif</div>
            <div style='color:#64748b'>{st.session_state.patient_case[:120]}{"…" if len(st.session_state.patient_case) > 120 else ""}</div>
          </div>
        </div>""", unsafe_allow_html=True)

        # Questions list
        QUESTIONS = [
            "Durée des symptômes",
            "Fièvre",
            "Douleur thoracique",
            "Difficultés respiratoires",
            "Médicaments actuels",
        ]
        st.markdown("<div class='card'><div class='card-title'>Guide des questions</div>", unsafe_allow_html=True)
        for i, q in enumerate(QUESTIONS):
            done = i < answered
            current = i == answered
            color = "#16a34a" if done else ("#2563eb" if current else "#94a3b8")
            icon = "✓" if done else ("→" if current else str(i+1))
            weight = "600" if current else "400"
            st.markdown(f"""<div style='display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid #f1f5f9;font-size:12px;color:{color};font-weight:{weight}'>
              <div style='width:18px;text-align:center;font-size:11px'>{icon}</div>
              <div>{q}</div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════
# ÉCRAN 3 — Validation médicale
# ════════════════════════════════════════════════════════════════════════

elif st.session_state.screen == "physician":
    topbar("Validation médicale", "Étape 3 sur 4 — Revue Human-in-the-Loop",
           "En attente du médecin", "warning")
    wf_bar()

    st.markdown("<div class='page-content'>", unsafe_allow_html=True)

    alert("Le workflow est en pause. Le médecin doit examiner la synthèse et compléter la validation avant de générer le rapport.", "warning")

    # Charger si absent
    if not st.session_state.preliminary_summary:
        sr = api_get(f"/consultation/{st.session_state.thread_id}")
        if sr:
            st.session_state.preliminary_summary = sr.get("preliminary_summary", "")
            st.session_state.intermediate_recommendation = sr.get("intermediate_recommendation", "")

    # Synthèse panels
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        st.markdown(f"""<div class='summary-panel'>
          <div class='summary-panel-header'>
            <span>📋</span> Synthèse clinique préliminaire
          </div>
          <div class='summary-panel-body'>{st.session_state.preliminary_summary or "Non disponible"}</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class='summary-panel'>
          <div class='summary-panel-header'>
            <span>💡</span> Recommandation intermédiaire
          </div>
          <div class='summary-panel-body'>{st.session_state.intermediate_recommendation or "Non disponible"}</div>
        </div>""", unsafe_allow_html=True)

    # Physician form
    st.markdown("<div class='physician-form-section'>", unsafe_allow_html=True)
    st.markdown("""<div style='font-size:15px;font-weight:700;color:#0f172a;margin-bottom:20px'>
      ✍️ Saisie de la décision médicale
    </div>""", unsafe_allow_html=True)

    col_f1, col_f2 = st.columns(2, gap="medium")
    with col_f1:
        st.markdown("<div class='form-field-label'>Traitement proposé</div>", unsafe_allow_html=True)
        treatment = st.text_area("", placeholder="Ex : Paracétamol 1g x3/jour si T° > 38.5°C, repos strict 48h…",
                                  height=110, key="treatment_field", label_visibility="collapsed")
    with col_f2:
        st.markdown("<div class='form-field-label'>Conduite à tenir</div>", unsafe_allow_html=True)
        conduct = st.text_area("", placeholder="Ex : Surveillance clinique à 48h, bilan NFS-CRP si persistance…",
                                height=110, key="conduct_field", label_visibility="collapsed")

    st.markdown("<div class='form-field-label'>Validation et commentaires médicaux <span class='required-badge'>OBLIGATOIRE</span></div>", unsafe_allow_html=True)
    validation_note = st.text_area("",
        placeholder="Ex : Tableau clinique compatible avec syndrome grippal. Pas d'élément de gravité. Prise en charge ambulatoire suffisante.",
        height=100, key="validation_field", label_visibility="collapsed")

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    if st.button("Valider et générer le rapport →", type="primary"):
        if not validation_note or not validation_note.strip():
            alert("Le champ 'Validation et commentaires médicaux' est obligatoire.", "error")
        else:
            with st.spinner("Génération du rapport final…"):
                resp = api_post("/consultation/resume", {
                    "thread_id": st.session_state.thread_id,
                    "action": "physician_review",
                    "treatment": treatment.strip(),
                    "conduct_to_hold": conduct.strip(),
                    "validation": validation_note.strip(),
                }, timeout=180)
            if resp:
                st.session_state.final_report = resp.get("final_report", "")
                st.session_state.screen = "report"
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════
# ÉCRAN 4 — Rapport final
# ════════════════════════════════════════════════════════════════════════

elif st.session_state.screen == "report":
    topbar("Rapport final", "Étape 4 sur 4 — Consultation terminée", "Complété", "success")
    wf_bar()

    st.markdown("<div class='page-content'>", unsafe_allow_html=True)

    alert("La consultation est terminée. Le rapport d'orientation clinique est disponible ci-dessous.", "success")

    if not st.session_state.final_report:
        with st.spinner("Chargement du rapport…"):
            rr = api_get(f"/consultation/{st.session_state.thread_id}/report")
            if rr:
                st.session_state.final_report = rr.get("final_report", "")

    if st.session_state.final_report:
        # Metadata row
        tid_short = st.session_state.thread_id[:8] if st.session_state.thread_id else "N/A"
        st.markdown(f"""<div class='info-grid'>
          <div class='info-cell'>
            <div class='info-cell-label'>Référence consultation</div>
            <div class='info-cell-value' style='font-family:JetBrains Mono,monospace;font-size:12px'>{tid_short}…</div>
          </div>
          <div class='info-cell'>
            <div class='info-cell-label'>Patient</div>
            <div class='info-cell-value'>{st.session_state.patient_name or "Anonyme"}</div>
          </div>
        </div>""", unsafe_allow_html=True)

        # Report
        st.markdown(f"""<div class='report-container'>
          <div class='report-header'>
            <div>
              <div class='report-header-title'>Rapport d'orientation clinique simulée</div>
              <div class='report-header-sub'>Système académique · Usage éducatif uniquement · LangGraph + Groq</div>
            </div>
            <div class='report-header-badge'>✓ Validé</div>
          </div>
          <div class='report-body'>{st.session_state.final_report}</div>
        </div>""", unsafe_allow_html=True)

        # Actions
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
        with col1:
            st.download_button(
                "⬇ Télécharger TXT",
                data=st.session_state.final_report.encode("utf-8"),
                file_name=f"rapport_clinique_{tid_short}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with col2:
            pdf = get_pdf_bytes(st.session_state.thread_id)
            if pdf:
                st.download_button(
                    "⬇ Télécharger PDF",
                    data=pdf,
                    file_name=f"rapport_clinique_{tid_short}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
        with col4:
            if st.button("＋ Nouvelle consultation", use_container_width=True):
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.rerun()
    else:
        alert("Rapport non disponible. La génération a peut-être échoué.", "error")
        if st.button("🔄 Rafraîchir"):
            st.rerun()

    # Legal footer
    st.markdown("""<div class='alert alert-warning' style='margin-top:24px'>
      <span class='alert-icon'>⚖️</span>
      <span><strong>Avertissement légal :</strong> Ce rapport est généré dans le cadre d'un projet académique universitaire.
      Il ne constitue pas un diagnostic médical et ne doit pas être utilisé à des fins cliniques réelles.
      Toute décision médicale doit être prise par un professionnel de santé qualifié.</span>
    </div>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
