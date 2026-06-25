from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import (
    AnalysisResponse,
    ExceptionSopRequest,
    InventoryBySkuRequest,
    OrderDeliveryRiskRequest,
    OrderStatusRequest,
    PurchaseArrivalRequest,
    PurchaseDelayImpactRequest,
    ToolResponse,
    WorkOrderReadinessRequest,
    WorkOrderRequest,
)
from app.services.analysis_service import (
    analyze_order_delivery_risk,
    analyze_purchase_delay_impact,
    analyze_work_order_readiness,
)
from app.services.auth_service import resolve_identity
from app.services.tool_service import execute_tool
from app.services.response_filter import filter_analysis_response, filter_tool_response

router = APIRouter(prefix="/api/tools", tags=["tools"])


def _identity(request: Request, username: str, role: str) -> dict[str, str]:
    return resolve_identity(request, fallback_username=username, fallback_role=role)


@router.post(
    "/query-order-status",
    response_model=ToolResponse,
    summary="Query simulated sales order status",
)
def query_order_status_endpoint(
    request: Request, payload: OrderStatusRequest, db: Session = Depends(get_db)
) -> ToolResponse:
    identity = _identity(request, payload.username, payload.role)
    response = execute_tool(
        db=db,
        username=identity["username"],
        role=identity["role"],
        tool_name="query_order_status",
        tool_args={"order_no": payload.order_no},
    )
    return filter_tool_response(response, identity["role"])[0]


@router.post(
    "/query-inventory-by-sku",
    response_model=ToolResponse,
    summary="Query simulated SKU inventory and batches",
)
def query_inventory_by_sku_endpoint(
    request: Request, payload: InventoryBySkuRequest, db: Session = Depends(get_db)
) -> ToolResponse:
    identity = _identity(request, payload.username, payload.role)
    response = execute_tool(
        db=db,
        username=identity["username"],
        role=identity["role"],
        tool_name="query_inventory_by_sku",
        tool_args={"sku_code": payload.sku_code},
    )
    return filter_tool_response(response, identity["role"])[0]


@router.post(
    "/query-work-order",
    response_model=ToolResponse,
    summary="Query simulated work order readiness data",
)
def query_work_order_endpoint(
    request: Request, payload: WorkOrderRequest, db: Session = Depends(get_db)
) -> ToolResponse:
    identity = _identity(request, payload.username, payload.role)
    response = execute_tool(
        db=db,
        username=identity["username"],
        role=identity["role"],
        tool_name="query_work_order",
        tool_args={"work_order_no": payload.work_order_no},
    )
    return filter_tool_response(response, identity["role"])[0]


@router.post(
    "/query-purchase-arrival",
    response_model=ToolResponse,
    summary="Query simulated purchase arrival status",
)
def query_purchase_arrival_endpoint(
    request: Request, payload: PurchaseArrivalRequest, db: Session = Depends(get_db)
) -> ToolResponse:
    identity = _identity(request, payload.username, payload.role)
    response = execute_tool(
        db=db,
        username=identity["username"],
        role=identity["role"],
        tool_name="query_purchase_arrival",
        tool_args={"purchase_order_no": payload.purchase_order_no},
    )
    return filter_tool_response(response, identity["role"])[0]


@router.post(
    "/query-exception-sop",
    response_model=ToolResponse,
    summary="Query exception SOP knowledge",
)
def query_exception_sop_endpoint(
    request: Request, payload: ExceptionSopRequest, db: Session = Depends(get_db)
) -> ToolResponse:
    identity = _identity(request, payload.username, payload.role)
    response = execute_tool(
        db=db,
        username=identity["username"],
        role=identity["role"],
        tool_name="query_exception_sop",
        tool_args={"question": payload.question},
    )
    return filter_tool_response(response, identity["role"])[0]


@router.post(
    "/analyze-order-delivery-risk",
    response_model=AnalysisResponse,
    summary="Analyze read-only order delivery risk",
)
def analyze_order_delivery_risk_endpoint(
    request: Request, payload: OrderDeliveryRiskRequest, db: Session = Depends(get_db)
) -> AnalysisResponse:
    identity = _identity(request, payload.username, payload.role)
    response = analyze_order_delivery_risk(
        db=db,
        username=identity["username"],
        role=identity["role"],
        order_no=payload.order_no,
    )
    return filter_analysis_response(response, identity["role"])[0]


@router.post(
    "/analyze-work-order-readiness",
    response_model=AnalysisResponse,
    summary="Analyze read-only work order material readiness",
)
def analyze_work_order_readiness_endpoint(
    request: Request, payload: WorkOrderReadinessRequest, db: Session = Depends(get_db)
) -> AnalysisResponse:
    identity = _identity(request, payload.username, payload.role)
    response = analyze_work_order_readiness(
        db=db,
        username=identity["username"],
        role=identity["role"],
        work_order_no=payload.work_order_no,
    )
    return filter_analysis_response(response, identity["role"])[0]


@router.post(
    "/analyze-purchase-delay-impact",
    response_model=AnalysisResponse,
    summary="Analyze read-only purchase delay impact",
)
def analyze_purchase_delay_impact_endpoint(
    request: Request, payload: PurchaseDelayImpactRequest, db: Session = Depends(get_db)
) -> AnalysisResponse:
    identity = _identity(request, payload.username, payload.role)
    response = analyze_purchase_delay_impact(
        db=db,
        username=identity["username"],
        role=identity["role"],
        purchase_order_no=payload.purchase_order_no,
    )
    return filter_analysis_response(response, identity["role"])[0]
