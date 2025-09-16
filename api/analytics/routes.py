"""Analytics API routes for poll statistics and insights."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api import models
from api.database import get_db
from api import auth
from api.analytics.services import AnalyticsService
from api.analytics.schemas import (
    AnalyticsOverview,
    PollAnalytics,
    VotingTrends,
    PopularPoll,
    AnalyticsTimeframe,
    PopularPollsRequest
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


def verify_poll_ownership(poll_id: int, current_user: models.User, db: Session) -> models.Poll:
    """
    Verify that the current user owns the specified poll.
    
    Args:
        poll_id: The ID of the poll to verify
        current_user: The authenticated user
        db: Database session
        
    Returns:
        The poll object if ownership is verified
        
    Raises:
        HTTPException: If poll not found or access denied
    """
    poll = db.query(models.Poll).filter(models.Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    
    if poll.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied: You don't own this poll")
    
    return poll


@router.get("/overview", response_model=AnalyticsOverview)
def get_analytics_overview(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
) -> AnalyticsOverview:
    """
    Get overall analytics summary for the current user's polls.
    
    Returns comprehensive metrics including:
    - Total polls created
    - Total votes received across all polls
    - Average engagement rate
    - Most popular poll
    - Recent activity feed
    - Monthly poll creation count
    
    Requires authentication.
    """
    try:
        analytics_service = AnalyticsService(db)
        return analytics_service.get_user_analytics_overview(current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate analytics overview: {str(e)}"
        )


@router.get("/polls/{poll_id}", response_model=PollAnalytics)
def get_poll_analytics(
    poll_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
) -> PollAnalytics:
    """
    Get detailed analytics for a specific poll.
    
    Returns comprehensive poll metrics including:
    - Vote distribution across options
    - Engagement rate and performance score
    - Unique voter count and vote velocity
    - Peak voting time analysis
    
    Args:
        poll_id: The ID of the poll to analyze
        
    Requires authentication and poll ownership.
    """
    # Verify poll ownership before proceeding
    verify_poll_ownership(poll_id, current_user, db)
    
    try:
        analytics_service = AnalyticsService(db)
        return analytics_service.get_poll_analytics(poll_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate poll analytics: {str(e)}"
        )


@router.get("/trends", response_model=VotingTrends)
def get_voting_trends(
    days: int = Query(default=7, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
) -> VotingTrends:
    """
    Get voting trends for the current user's polls over a specified time period.
    
    Analyzes voting patterns including:
    - Daily vote counts and unique voters
    - Popular voting times (hours)
    - Overall engagement trend (increasing/decreasing/stable)
    - Peak activity days
    
    Args:
        days: Number of days to analyze (1-365, default: 7)
        
    Requires authentication.
    """
    try:
        analytics_service = AnalyticsService(db)
        return analytics_service.get_voting_trends(current_user.id, days)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate voting trends: {str(e)}"
        )


@router.get("/popular", response_model=List[PopularPoll])
def get_popular_polls(
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of polls to return"),
    timeframe: str = Query(
        default="week",
        pattern="^(day|week|month|year|all)$",
        description="Time period for popularity calculation"
    ),
    db: Session = Depends(get_db)
) -> List[PopularPoll]:
    """
    Get the most popular polls across the platform (public endpoint).
    
    Returns polls ranked by vote count within the specified timeframe.
    Includes engagement metrics and creator information.
    
    Args:
        limit: Maximum number of polls to return (1-50, default: 10)
        timeframe: Time period - 'day', 'week', 'month', 'year', or 'all'
        
    This is a public endpoint - no authentication required.
    """
    try:
        analytics_service = AnalyticsService(db)
        return analytics_service.get_popular_polls(limit, timeframe)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch popular polls: {str(e)}"
        )


@router.get("/polls/{poll_id}/engagement", response_model=dict)
def get_poll_engagement_details(
    poll_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
) -> dict:
    """
    Get detailed engagement metrics for a specific poll.
    
    Provides advanced engagement analysis including:
    - Views to votes conversion rate
    - Voting pattern analysis
    - Comparative performance metrics
    
    Args:
        poll_id: The ID of the poll to analyze
        
    Requires authentication and poll ownership.
    """
    # Verify poll ownership
    poll = verify_poll_ownership(poll_id, current_user, db)
    
    try:
        analytics_service = AnalyticsService(db)
        
        # Get basic poll analytics
        poll_analytics = analytics_service.get_poll_analytics(poll_id)
        
        # Calculate additional engagement metrics
        total_votes = poll_analytics.total_votes
        total_views = poll_analytics.total_views
        
        # Views to votes conversion rate
        conversion_rate = (total_votes / total_views * 100) if total_views > 0 else 0.0
        
        # Calculate poll age in hours
        poll_age_hours = (poll_analytics.created_at.timestamp() - poll.created_at.timestamp()) / 3600
        
        # Engagement velocity (engagement events per hour)
        engagement_velocity = (total_votes + total_views) / poll_age_hours if poll_age_hours > 0 else 0.0
        
        return {
            "poll_id": poll_id,
            "basic_metrics": {
                "total_votes": total_votes,
                "total_views": total_views,
                "unique_voters": poll_analytics.unique_voters,
                "engagement_rate": poll_analytics.engagement_rate
            },
            "advanced_metrics": {
                "conversion_rate": round(conversion_rate, 2),
                "engagement_velocity": round(engagement_velocity, 2),
                "vote_velocity": poll_analytics.vote_velocity,
                "performance_score": poll_analytics.performance_score
            },
            "temporal_analysis": {
                "poll_age_hours": round(poll_age_hours, 2),
                "peak_voting_time": poll_analytics.peak_voting_time,
                "created_at": poll_analytics.created_at
            },
            "vote_distribution": poll_analytics.vote_distribution
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate engagement details: {str(e)}"
        )


@router.get("/user/summary", response_model=dict)
def get_user_analytics_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
) -> dict:
    """
    Get a quick analytics summary for the current user.
    
    Provides key metrics at a glance:
    - Total polls and votes
    - Best performing poll
    - Recent activity count
    - Account statistics
    
    Requires authentication.
    """
    try:
        analytics_service = AnalyticsService(db)
        overview = analytics_service.get_user_analytics_overview(current_user.id)
        
        # Calculate additional summary metrics
        avg_votes_per_poll = (
            overview.total_votes_received / overview.total_polls
            if overview.total_polls > 0 else 0
        )
        
        return {
            "user_id": current_user.id,
            "username": current_user.username,
            "account_created": current_user.created_at,
            "poll_statistics": {
                "total_polls": overview.total_polls,
                "polls_this_month": overview.polls_created_this_month,
                "total_votes_received": overview.total_votes_received,
                "average_votes_per_poll": round(avg_votes_per_poll, 1)
            },
            "engagement_metrics": {
                "average_engagement_rate": round(overview.average_engagement_rate, 2),
                "total_poll_views": overview.total_poll_views
            },
            "top_poll": {
                "most_popular": overview.most_popular_poll
            },
            "activity": {
                "recent_activity_count": len(overview.recent_activity),
                "last_activity": (
                    overview.recent_activity[0].timestamp
                    if overview.recent_activity else None
                )
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate user summary: {str(e)}"
        )