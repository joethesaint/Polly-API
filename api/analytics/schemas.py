"""Analytics Pydantic schemas for API responses."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class PollSummary(BaseModel):
    """Basic poll information for analytics."""
    id: int
    question: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ActivityItem(BaseModel):
    """Individual activity item for recent activity feed."""
    poll_id: int
    poll_question: str
    activity_type: str = Field(..., description="Type of activity: 'vote', 'create', 'view'")
    timestamp: datetime
    count: int = Field(default=1, description="Number of activities of this type")


class DailyVoteCount(BaseModel):
    """Daily vote count for trend analysis."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    vote_count: int
    unique_voters: int


class AnalyticsOverview(BaseModel):
    """Overall analytics summary for a user's polls."""
    total_polls: int = Field(..., description="Total number of polls created by user")
    total_votes_received: int = Field(..., description="Total votes across all user's polls")
    average_engagement_rate: float = Field(..., description="Average engagement rate as percentage")
    most_popular_poll: Optional[PollSummary] = Field(None, description="Poll with highest vote count")
    recent_activity: List[ActivityItem] = Field(default_factory=list, description="Recent activity on user's polls")
    polls_created_this_month: int = Field(..., description="Number of polls created in current month")
    total_poll_views: int = Field(default=0, description="Total views across all polls")


class PollAnalytics(BaseModel):
    """Detailed analytics for a specific poll."""
    poll_id: int
    poll_question: str
    total_votes: int
    engagement_rate: float = Field(..., description="Engagement rate as percentage (votes/views * 100)")
    vote_distribution: Dict[str, int] = Field(..., description="Vote count per option")
    performance_score: float = Field(..., description="Overall performance score (0-100)")
    created_at: datetime
    peak_voting_time: Optional[datetime] = Field(None, description="Time when most votes were cast")
    total_views: int = Field(default=0, description="Total number of poll views")
    unique_voters: int = Field(..., description="Number of unique users who voted")
    vote_velocity: float = Field(default=0.0, description="Votes per hour since creation")


class VotingTrends(BaseModel):
    """Voting trends analysis over a time period."""
    timeframe: str = Field(..., description="Time period analyzed (e.g., 'week', 'month')")
    daily_votes: List[DailyVoteCount] = Field(..., description="Daily vote counts for the period")
    popular_times: List[str] = Field(..., description="Most popular voting hours (24h format)")
    engagement_trend: str = Field(..., description="Overall trend: 'increasing', 'decreasing', 'stable'")
    total_votes_period: int = Field(..., description="Total votes in the analyzed period")
    average_daily_votes: float = Field(..., description="Average votes per day in period")
    peak_day: Optional[str] = Field(None, description="Day with highest vote count")


class PopularPoll(BaseModel):
    """Popular poll information for public analytics."""
    poll_id: int
    question: str
    vote_count: int
    engagement_rate: float
    created_at: datetime
    creator_username: str = Field(..., description="Username of poll creator")
    option_count: int = Field(..., description="Number of options in the poll")
    
    class Config:
        from_attributes = True


class EngagementMetrics(BaseModel):
    """Detailed engagement metrics for analytics."""
    views_to_votes_ratio: float = Field(..., description="Ratio of views that converted to votes")
    average_time_to_vote: Optional[float] = Field(None, description="Average time from view to vote in minutes")
    bounce_rate: float = Field(..., description="Percentage of single-page views")
    return_voter_rate: float = Field(default=0.0, description="Percentage of voters who vote on multiple polls")


class PollPerformanceComparison(BaseModel):
    """Comparison of poll performance metrics."""
    current_poll: PollAnalytics
    user_average: Dict[str, float] = Field(..., description="User's average metrics for comparison")
    platform_average: Dict[str, float] = Field(..., description="Platform-wide averages for comparison")
    percentile_rank: float = Field(..., description="Poll's percentile rank compared to all polls")


class AnalyticsError(BaseModel):
    """Error response for analytics endpoints."""
    error_code: str
    message: str
    details: Optional[Dict] = None


# Request schemas for analytics endpoints
class AnalyticsTimeframe(BaseModel):
    """Request schema for timeframe-based analytics."""
    days: int = Field(default=7, ge=1, le=365, description="Number of days to analyze")
    

class PopularPollsRequest(BaseModel):
    """Request schema for popular polls endpoint."""
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of polls to return")
    timeframe: str = Field(default="week", pattern="^(day|week|month|year|all)$", description="Time period for popularity calculation")
    category: Optional[str] = Field(None, description="Filter by poll category if available")