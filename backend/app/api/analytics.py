from typing import List, Dict
from collections import defaultdict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.referral import Referral, ReferralStatus
from app.models.job_position import JobPosition
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsResponse,
    StatusFunnelStep,
    DepartmentMetric,
    MonthlyTrend,
    TopReferrer,
)
from app.api.deps import require_hr_admin

router = APIRouter(prefix="/hr/analytics", tags=["HR Analytics"])


@router.get("", response_model=AnalyticsResponse)
async def get_referral_analytics(
    db: Session = Depends(get_db),
    hr_user: User = Depends(require_hr_admin),
):
    """
    Generate comprehensive referral analytics, funnel conversions,
    department statistics, and top referrers leaderboard.
    """
    all_referrals = db.query(Referral).all()
    total = len(all_referrals)

    # Status breakdown counts
    counts: Dict[str, int] = defaultdict(int)
    for r in all_referrals:
        counts[r.status] += 1

    hired_count = counts.get(ReferralStatus.HIRED.value, 0)
    rejected_count = counts.get(ReferralStatus.REJECTED.value, 0)
    withdrawn_count = counts.get(ReferralStatus.WITHDRAWN.value, 0)
    active_count = total - (hired_count + rejected_count + withdrawn_count)

    # Pipeline Funnel
    funnel_stages = [
        ReferralStatus.SUBMITTED.value,
        ReferralStatus.UNDER_REVIEW.value,
        ReferralStatus.SHORTLISTED.value,
        ReferralStatus.INTERVIEW.value,
        ReferralStatus.SELECTED.value,
        ReferralStatus.HIRED.value,
    ]
    funnel: List[StatusFunnelStep] = []
    for stage in funnel_stages:
        st_count = counts.get(stage, 0)
        pct = round((st_count / total * 100), 1) if total > 0 else 0.0
        funnel.append(StatusFunnelStep(status=stage, count=st_count, percentage=pct))

    # Department breakdown
    dept_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "hired": 0})
    for r in all_referrals:
        dept = r.position.department if r.position else "Unassigned"
        dept_stats[dept]["total"] += 1
        if r.status == ReferralStatus.HIRED.value:
            dept_stats[dept]["hired"] += 1

    dept_metrics = [
        DepartmentMetric(
            department=dept,
            total_referrals=data["total"],
            hired_count=data["hired"],
        )
        for dept, data in sorted(dept_stats.items(), key=lambda x: x[1]["total"], reverse=True)
    ]

    # Monthly trends (last 6 months)
    month_counts: Dict[str, int] = defaultdict(int)
    for r in all_referrals:
        month_key = r.created_at.strftime("%b %Y")
        month_counts[month_key] += 1

    monthly_trends = [
        MonthlyTrend(month=m, count=c)
        for m, c in month_counts.items()
    ]

    # Top Referrers Leaderboard
    referrer_stats: Dict[str, Dict[str, any]] = defaultdict(
        lambda: {"user_id": "", "name": "", "email": "", "total": 0, "hired": 0}
    )
    for r in all_referrals:
        uid = r.referred_by_user_id
        if r.referred_by:
            referrer_stats[uid]["user_id"] = uid
            referrer_stats[uid]["name"] = r.referred_by.name
            referrer_stats[uid]["email"] = r.referred_by.email
            referrer_stats[uid]["total"] += 1
            if r.status == ReferralStatus.HIRED.value:
                referrer_stats[uid]["hired"] += 1

    top_referrers = [
        TopReferrer(
            user_id=data["user_id"],
            user_name=data["name"],
            user_email=data["email"],
            referral_count=data["total"],
            hired_count=data["hired"],
        )
        for data in sorted(referrer_stats.values(), key=lambda x: (x["hired"], x["total"]), reverse=True)[:10]
    ]

    return AnalyticsResponse(
        total_referrals=total,
        active_referrals=active_count,
        hired_referrals=hired_count,
        rejected_referrals=rejected_count,
        withdrawn_referrals=withdrawn_count,
        funnel=funnel,
        by_department=dept_metrics,
        monthly_trends=monthly_trends,
        top_referrers=top_referrers,
    )
