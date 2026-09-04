from typing import List, Dict
from pydantic import BaseModel


class StatusFunnelStep(BaseModel):
    status: str
    count: int
    percentage: float


class DepartmentMetric(BaseModel):
    department: str
    total_referrals: int
    hired_count: int


class MonthlyTrend(BaseModel):
    month: str
    count: int


class TopReferrer(BaseModel):
    user_id: str
    user_name: str
    user_email: str
    referral_count: int
    hired_count: int


class AnalyticsResponse(BaseModel):
    total_referrals: int
    active_referrals: int
    hired_referrals: int
    rejected_referrals: int
    withdrawn_referrals: int
    funnel: List[StatusFunnelStep]
    by_department: List[DepartmentMetric]
    monthly_trends: List[MonthlyTrend]
    top_referrers: List[TopReferrer]
