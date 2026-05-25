import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..database import get_db
from ..models.workspace import Workspace, WorkspacePlan, WorkspaceSubscriptionStatus
from ..models.user import User
from .deps import get_current_user, get_current_workspace
from ..config import settings

router = APIRouter()

stripe.api_key = settings.stripe_secret_key


class CheckoutRequest(BaseModel):
    plan: str


@router.get("/status")
def billing_status(workspace: Workspace = Depends(get_current_workspace)):
    return {
        "plan": workspace.plan,
        "subscription_status": workspace.subscription_status,
        "stripe_customer_id": workspace.stripe_customer_id,
    }


@router.post("/checkout")
def create_checkout(
    data: CheckoutRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
):
    price_map = {
        "pro": settings.stripe_pro_price_id,
        "agency": settings.stripe_agency_price_id,
    }
    if data.plan not in price_map:
        raise HTTPException(status_code=400, detail="Invalid plan. Choose 'pro' or 'agency'.")

    price_id = price_map[data.plan]
    if not price_id:
        raise HTTPException(status_code=503, detail="Billing not configured")

    if not workspace.stripe_customer_id:
        customer = stripe.Customer.create(
            email=user.email,
            name=workspace.name,
            metadata={"workspace_id": str(workspace.id)},
        )
        workspace.stripe_customer_id = customer.id
        db.commit()

    session = stripe.checkout.Session.create(
        customer=workspace.stripe_customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        subscription_data={"metadata": {"workspace_id": str(workspace.id)}},
        success_url=f"{settings.frontend_url}/dashboard/billing?success=1",
        cancel_url=f"{settings.frontend_url}/dashboard/billing?cancelled=1",
    )
    return {"checkout_url": session.url}


@router.get("/portal")
def billing_portal(workspace: Workspace = Depends(get_current_workspace)):
    if not workspace.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing account found. Subscribe first.")
    session = stripe.billing_portal.Session.create(
        customer=workspace.stripe_customer_id,
        return_url=f"{settings.frontend_url}/dashboard/billing",
    )
    return {"portal_url": session.url}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.stripe_webhook_secret)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    event_type = event["type"]
    sub_obj = event["data"]["object"]

    if event_type in ("customer.subscription.created", "customer.subscription.updated"):
        workspace_id_str = sub_obj.get("metadata", {}).get("workspace_id")
        if workspace_id_str:
            workspace = db.query(Workspace).filter(Workspace.id == int(workspace_id_str)).first()
            if workspace:
                workspace.stripe_subscription_id = sub_obj["id"]
                status = sub_obj.get("status", "inactive")
                workspace.subscription_status = (
                    WorkspaceSubscriptionStatus.active if status == "active"
                    else WorkspaceSubscriptionStatus.inactive
                )
                price_id = (
                    sub_obj.get("items", {})
                    .get("data", [{}])[0]
                    .get("price", {})
                    .get("id", "")
                )
                if price_id == settings.stripe_pro_price_id:
                    workspace.plan = WorkspacePlan.pro
                elif price_id == settings.stripe_agency_price_id:
                    workspace.plan = WorkspacePlan.agency
                db.commit()

    elif event_type == "customer.subscription.deleted":
        workspace_id_str = sub_obj.get("metadata", {}).get("workspace_id")
        if workspace_id_str:
            workspace = db.query(Workspace).filter(Workspace.id == int(workspace_id_str)).first()
            if workspace:
                workspace.plan = WorkspacePlan.free
                workspace.subscription_status = WorkspaceSubscriptionStatus.inactive
                workspace.stripe_subscription_id = None
                db.commit()

    return {"status": "ok"}
