from typing import Any

from pydantic import BaseModel, Field


class ActorRequest(BaseModel):
    username: str = "demo_admin"
    role: str = "admin"


class ToolResponse(BaseModel):
    success: bool
    permission_allowed: bool
    tool_name: str
    data: Any | None = None
    message: str
    manual_confirmation_required: bool = True


class ChatRequest(ActorRequest):
    question: str


class ChatResponse(BaseModel):
    success: bool
    question: str
    answer: str
    checked_data: list[str]
    called_tools: list[ToolResponse]
    business_conclusion: str
    suggested_next_action: str
    intent: str = ""
    entities: dict[str, Any] = Field(default_factory=dict)
    execution_trace: list[dict[str, Any]] = Field(default_factory=list)
    risk_level: str = ""
    evidence: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    risk_factors: list[str] = Field(default_factory=list)
    requires_human_review: bool = False
    manual_review_reason: list[str] = Field(default_factory=list)
    decision_record: dict[str, Any] = Field(default_factory=dict)
    manual_confirmation_required: bool = True


class AnalysisResponse(BaseModel):
    success: bool
    permission_allowed: bool
    analysis_name: str
    checked_data: list[str]
    called_tools: list[ToolResponse]
    risk_level: str
    evidence: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    risk_factors: list[str] = Field(default_factory=list)
    requires_human_review: bool = False
    manual_review_reason: list[str] = Field(default_factory=list)
    business_conclusion: str
    suggested_next_action: str
    message: str
    manual_confirmation_required: bool = True


class OrderStatusRequest(ActorRequest):
    order_no: str


class InventoryBySkuRequest(ActorRequest):
    sku_code: str


class WorkOrderRequest(ActorRequest):
    work_order_no: str


class PurchaseArrivalRequest(ActorRequest):
    purchase_order_no: str


class ExceptionSopRequest(ActorRequest):
    question: str


class OrderDeliveryRiskRequest(ActorRequest):
    order_no: str


class WorkOrderReadinessRequest(ActorRequest):
    work_order_no: str


class PurchaseDelayImpactRequest(ActorRequest):
    purchase_order_no: str


class KnowledgeSearchResponse(BaseModel):
    success: bool
    permission_allowed: bool
    query: str
    results: list[dict[str, Any]]
    message: str
    manual_confirmation_required: bool = True


class AdminListResponse(BaseModel):
    success: bool
    data: list[dict[str, Any]]


class GenericResponse(BaseModel):
    success: bool
    message: str
    data: Any | None = None
