from typing import Optional
from pydantic import BaseModel, Field
from langgraph.graph import MessagesState


class PhysicianReviewData(BaseModel):
    treatment: str = Field(default="")
    conduct_to_hold: str = Field(default="")
    validation: str = Field(default="")
    reviewed_at: Optional[str] = Field(default=None)


class ClinicalWorkflowState(MessagesState):
    thread_id: str = Field(default="")
    patient_initial_case: str = Field(default="")
    questions: list[str] = Field(default_factory=list)
    answers: list[str] = Field(default_factory=list)
    current_question_index: int = Field(default=0)
    preliminary_summary: str = Field(default="")
    intermediate_recommendation: str = Field(default="")
    physician_review: Optional[PhysicianReviewData] = Field(default=None)
    final_report: str = Field(default="")
    next_step: str = Field(default="diagnostic_agent")
    workflow_status: str = Field(default="started")
    error_message: Optional[str] = Field(default=None)
    mcp_care_recommendations: list[str] = Field(default_factory=list)
