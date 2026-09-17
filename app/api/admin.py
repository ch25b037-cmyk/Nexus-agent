# app/api/admin.py
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional


from app.api.deps import get_db
from app.models.cost import TokenUsage
from app.models.user import User
from app.api.deps import get_optional_user
from app.services.schedulers import autonomous_crawl_and_refresh

router = APIRouter(prefix="/api/admin", tags=["Admin / Background"])


@router.get("/costs")
def get_cost_dashboard(
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Multi-tenant Token Usage:
    Returns the active user's personal token spend if logged in,
    or overall platform totals.
    """
    query = db.query(TokenUsage)
    
    # If user is logged in, show THEIR personal spend!
    if current_user:
        query = query.filter((TokenUsage.user_id == current_user.id) | (TokenUsage.user_id == None))

    total_tokens = query.with_entities(func.sum(TokenUsage.total_tokens)).scalar() or 0
    total_cost = query.with_entities(func.sum(TokenUsage.cost_inr)).scalar() or 0.0

    features = query.with_entities(
        TokenUsage.feature,
        func.sum(TokenUsage.total_tokens).label("tokens"),
        func.sum(TokenUsage.cost_inr).label("cost")
    ).group_by(TokenUsage.feature).all()

    return {
        "user_email": current_user.email if current_user else "Platform Total",
        "total_tokens": int(total_tokens),
        "total_cost_inr": f"₹{round(total_cost, 2)}",
        "features": [
            {
                "feature": f[0],
                "tokens": int(f[1]),
                "cost_inr": f"₹{round(f[2], 2)}"
            }
            for f in features
        ]
    }


@router.post("/trigger-cron")
def trigger_cron_manually(background_tasks: BackgroundTasks):
    """
    Manually triggers the autonomous ingestion cron job in the background.
    Perfect for live demonstrations!
    """
    background_tasks.add_task(autonomous_crawl_and_refresh)
    return {"message": "Autonomous cron job triggered in background!"}