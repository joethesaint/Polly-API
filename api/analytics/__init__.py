"""Analytics module for Polly-API.

Provides comprehensive analytics and insights for polls including:
- User analytics overview and summaries
- Individual poll performance metrics
- Voting trends and pattern analysis
- Popular polls across the platform
- Engagement metrics and conversion rates
"""

from .services import AnalyticsService
from .routes import router as analytics_router
from .schemas import (
    AnalyticsOverview,
    PollAnalytics,
    VotingTrends,
    PopularPoll,
    ActivityItem,
    DailyVoteCount,
    PollSummary,
    EngagementMetrics,
    PollPerformanceComparison,
    AnalyticsError,
    AnalyticsTimeframe,
    PopularPollsRequest
)

__all__ = [
    "AnalyticsService",
    "analytics_router",
    "AnalyticsOverview",
    "PollAnalytics",
    "VotingTrends",
    "PopularPoll",
    "ActivityItem",
    "DailyVoteCount",
    "PollSummary",
    "EngagementMetrics",
    "PollPerformanceComparison",
    "AnalyticsError",
    "AnalyticsTimeframe",
    "PopularPollsRequest"
]