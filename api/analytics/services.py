"""Analytics service layer for business logic and calculations."""

import logging
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from functools import lru_cache

from api import models
from api.analytics.schemas import (
    AnalyticsOverview, PollAnalytics, VotingTrends, PopularPoll,
    ActivityItem, DailyVoteCount, PollSummary, EngagementMetrics
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service class for analytics calculations and data aggregation."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_analytics_overview(self, user_id: int) -> AnalyticsOverview:
        """
        Get comprehensive analytics overview for a user's polls.
        
        Args:
            user_id: The ID of the user to analyze
            
        Returns:
            AnalyticsOverview with aggregated metrics
            
        Raises:
            ValueError: If user_id is invalid
        """
        try:
            if user_id <= 0:
                raise ValueError("User ID must be positive")
            
            logger.info(f"Generating analytics overview for user {user_id}")
            
            # Optimized query to get poll count and basic stats in one go
            user_polls = self.db.query(models.Poll).filter(models.Poll.owner_id == user_id).all()
            total_polls = len(user_polls)
            
            if total_polls == 0:
                logger.info(f"No polls found for user {user_id}")
                return AnalyticsOverview(
                    total_polls=0,
                    total_votes_received=0,
                    average_engagement_rate=0.0,
                    most_popular_poll=None,
                    recent_activity=[],
                    polls_created_this_month=0,
                    total_poll_views=0
                )
            
            # Calculate total votes across all user's polls (optimized query)
            total_votes = self.db.query(func.count(models.Vote.id))\
                .join(models.Option)\
                .join(models.Poll)\
            .filter(models.Poll.owner_id == user_id)\
            .scalar() or 0
        
        # Calculate total views (assuming view_count field exists)
        total_views = sum(getattr(poll, 'view_count', 0) for poll in user_polls)
        
        # Calculate average engagement rate
        avg_engagement = self._calculate_average_engagement_rate(user_polls)
        
        # Find most popular poll
        most_popular = self._get_most_popular_poll(user_polls)
        
        # Get recent activity
        recent_activity = self._get_recent_activity(user_id, limit=10)
        
        # Count polls created this month
        current_month_start = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        polls_this_month = self.db.query(func.count(models.Poll.id))\
            .filter(
                and_(
                    models.Poll.owner_id == user_id,
                    models.Poll.created_at >= current_month_start
                )
            ).scalar() or 0
        
            return AnalyticsOverview(
                total_polls=total_polls,
                total_votes_received=total_votes,
                average_engagement_rate=avg_engagement,
                most_popular_poll=most_popular,
                recent_activity=recent_activity,
                polls_created_this_month=polls_this_month,
                total_poll_views=total_views
            )
            
        except ValueError as e:
            logger.error(f"Validation error in get_user_analytics_overview: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_user_analytics_overview for user {user_id}: {e}")
            raise RuntimeError(f"Failed to generate analytics overview: {str(e)}")
    
    def get_poll_analytics(self, poll_id: int) -> PollAnalytics:
        """
        Get detailed analytics for a specific poll.
        
        Args:
            poll_id: The ID of the poll to analyze
            
        Returns:
            PollAnalytics with detailed metrics
            
        Raises:
            ValueError: If poll not found
        """
        poll = self.db.query(models.Poll).filter(models.Poll.id == poll_id).first()
        if not poll:
            raise ValueError(f"Poll with ID {poll_id} not found")
        
        # Get vote distribution
        vote_distribution = self._get_vote_distribution(poll_id)
        total_votes = sum(vote_distribution.values())
        
        # Calculate engagement rate
        poll_views = getattr(poll, 'view_count', 0)
        engagement_rate = (total_votes / poll_views * 100) if poll_views > 0 else 0.0
        
        # Calculate performance score
        performance_score = self._calculate_poll_performance_score(poll_id)
        
        # Get unique voters count
        unique_voters = self.db.query(func.count(func.distinct(models.Vote.user_id)))\
            .join(models.Option)\
            .filter(models.Option.poll_id == poll_id)\
            .scalar() or 0
        
        # Calculate vote velocity (votes per hour)
        hours_since_creation = (datetime.now(UTC) - poll.created_at).total_seconds() / 3600
        vote_velocity = total_votes / hours_since_creation if hours_since_creation > 0 else 0.0
        
        # Find peak voting time (simplified - could be enhanced)
        peak_voting_time = self._get_peak_voting_time(poll_id)
        
        return PollAnalytics(
            poll_id=poll_id,
            poll_question=poll.question,
            total_votes=total_votes,
            engagement_rate=engagement_rate,
            vote_distribution=vote_distribution,
            performance_score=performance_score,
            created_at=poll.created_at,
            peak_voting_time=peak_voting_time,
            total_views=poll_views,
            unique_voters=unique_voters,
            vote_velocity=vote_velocity
        )
    
    def get_voting_trends(self, user_id: int, days: int = 7) -> VotingTrends:
        """
        Get voting trends for a user's polls over specified time period.
        
        Args:
            user_id: The ID of the user
            days: Number of days to analyze
            
        Returns:
            VotingTrends with trend analysis
        """
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=days)
        
        # Get daily vote counts
        daily_votes = self._get_daily_vote_counts(user_id, start_date, end_date)
        
        # Calculate total votes in period
        total_votes = sum(day.vote_count for day in daily_votes)
        
        # Calculate average daily votes
        avg_daily_votes = total_votes / days if days > 0 else 0.0
        
        # Determine engagement trend
        engagement_trend = self._calculate_engagement_trend(daily_votes)
        
        # Find peak day
        peak_day = max(daily_votes, key=lambda x: x.vote_count).date if daily_votes else None
        
        # Get popular voting times (simplified)
        popular_times = self._get_popular_voting_times(user_id, start_date, end_date)
        
        timeframe_str = f"{days} days" if days != 7 else "week"
        
        return VotingTrends(
            timeframe=timeframe_str,
            daily_votes=daily_votes,
            popular_times=popular_times,
            engagement_trend=engagement_trend,
            total_votes_period=total_votes,
            average_daily_votes=avg_daily_votes,
            peak_day=peak_day
        )
    
    def get_popular_polls(self, limit: int = 10, timeframe: str = "week") -> List[PopularPoll]:
        """
        Get most popular polls across the platform.
        
        Args:
            limit: Maximum number of polls to return
            timeframe: Time period for popularity calculation
            
        Returns:
            List of PopularPoll objects
        """
        cutoff_date = self._calculate_cutoff_date(timeframe)
        
        # Query for popular polls with vote counts
        popular_polls_query = self.db.query(
            models.Poll,
            func.count(models.Vote.id).label('vote_count')
        ).join(models.Option)\
         .join(models.Vote)\
         .join(models.User, models.Poll.owner_id == models.User.id)\
         .filter(models.Poll.created_at >= cutoff_date)\
         .group_by(models.Poll.id)\
         .order_by(desc('vote_count'))\
         .limit(limit)
        
        results = []
        for poll, vote_count in popular_polls_query:
            # Calculate engagement rate
            poll_views = getattr(poll, 'view_count', 0)
            engagement_rate = (vote_count / poll_views * 100) if poll_views > 0 else 0.0
            
            # Count options
            option_count = self.db.query(func.count(models.Option.id))\
                .filter(models.Option.poll_id == poll.id).scalar() or 0
            
            results.append(PopularPoll(
                poll_id=poll.id,
                question=poll.question,
                vote_count=vote_count,
                engagement_rate=engagement_rate,
                created_at=poll.created_at,
                creator_username=poll.owner.username,
                option_count=option_count
            ))
        
        return results
    
    # Private helper methods
    
    def _get_vote_distribution(self, poll_id: int) -> Dict[str, int]:
        """Get vote count distribution for a poll's options."""
        results = self.db.query(
            models.Option.text,
            func.count(models.Vote.id).label('vote_count')
        ).outerjoin(models.Vote, models.Option.id == models.Vote.option_id)\
         .filter(models.Option.poll_id == poll_id)\
         .group_by(models.Option.id, models.Option.text)\
         .all()
        
        return {option_text: vote_count for option_text, vote_count in results}
    
    def _calculate_average_engagement_rate(self, polls: List[models.Poll]) -> float:
        """Calculate average engagement rate across polls."""
        if not polls:
            return 0.0
        
        total_engagement = 0.0
        valid_polls = 0
        
        for poll in polls:
            poll_views = getattr(poll, 'view_count', 0)
            if poll_views > 0:
                vote_count = self.db.query(func.count(models.Vote.id))\
                    .join(models.Option)\
                    .filter(models.Option.poll_id == poll.id)\
                    .scalar() or 0
                
                engagement_rate = (vote_count / poll_views) * 100
                total_engagement += engagement_rate
                valid_polls += 1
        
        return total_engagement / valid_polls if valid_polls > 0 else 0.0
    
    def _get_most_popular_poll(self, polls: List[models.Poll]) -> Optional[PollSummary]:
        """Find the most popular poll by vote count."""
        if not polls:
            return None
        
        max_votes = 0
        most_popular = None
        
        for poll in polls:
            vote_count = self.db.query(func.count(models.Vote.id))\
                .join(models.Option)\
                .filter(models.Option.poll_id == poll.id)\
                .scalar() or 0
            
            if vote_count > max_votes:
                max_votes = vote_count
                most_popular = poll
        
        if most_popular:
            return PollSummary(
                id=most_popular.id,
                question=most_popular.question,
                created_at=most_popular.created_at
            )
        
        return None
    
    def _get_recent_activity(self, user_id: int, limit: int = 10) -> List[ActivityItem]:
        """Get recent activity on user's polls."""
        # Get recent votes on user's polls
        recent_votes = self.db.query(
            models.Vote.created_at,
            models.Poll.id,
            models.Poll.question
        ).join(models.Option)\
         .join(models.Poll)\
         .filter(models.Poll.owner_id == user_id)\
         .order_by(desc(models.Vote.created_at))\
         .limit(limit)\
         .all()
        
        activities = []
        for vote_time, poll_id, poll_question in recent_votes:
            activities.append(ActivityItem(
                poll_id=poll_id,
                poll_question=poll_question,
                activity_type="vote",
                timestamp=vote_time,
                count=1
            ))
        
        return activities
    
    def _calculate_poll_performance_score(self, poll_id: int) -> float:
        """
        Calculate overall performance score for a poll (0-100).
        
        Factors: vote count, engagement rate, recency, unique voters
        """
        poll = self.db.query(models.Poll).filter(models.Poll.id == poll_id).first()
        if not poll:
            return 0.0
        
        # Get basic metrics
        vote_count = self.db.query(func.count(models.Vote.id))\
            .join(models.Option)\
            .filter(models.Option.poll_id == poll_id)\
            .scalar() or 0
        
        poll_views = getattr(poll, 'view_count', 0)
        engagement_rate = (vote_count / poll_views) if poll_views > 0 else 0
        
        # Recency factor (newer polls get slight boost)
        days_old = (datetime.now(UTC) - poll.created_at).days
        recency_factor = max(0, 1 - (days_old / 30))  # Decay over 30 days
        
        # Combine factors (simplified scoring)
        score = min(100, (
            (vote_count * 10) +  # Vote count weight
            (engagement_rate * 50) +  # Engagement weight
            (recency_factor * 20)  # Recency weight
        ))
        
        return round(score, 2)
    
    def _get_peak_voting_time(self, poll_id: int) -> Optional[datetime]:
        """Find the time when most votes were cast (simplified implementation)."""
        # This is a simplified version - could be enhanced with hourly analysis
        peak_vote = self.db.query(models.Vote.created_at)\
            .join(models.Option)\
            .filter(models.Option.poll_id == poll_id)\
            .order_by(desc(models.Vote.created_at))\
            .first()
        
        return peak_vote[0] if peak_vote else None
    
    def _get_daily_vote_counts(self, user_id: int, start_date: datetime, end_date: datetime) -> List[DailyVoteCount]:
        """Get daily vote counts for user's polls in date range."""
        # Query votes grouped by date
        daily_counts = self.db.query(
            func.date(models.Vote.created_at).label('vote_date'),
            func.count(models.Vote.id).label('vote_count'),
            func.count(func.distinct(models.Vote.user_id)).label('unique_voters')
        ).join(models.Option)\
         .join(models.Poll)\
         .filter(
             and_(
                 models.Poll.owner_id == user_id,
                 models.Vote.created_at >= start_date,
                 models.Vote.created_at <= end_date
             )
         ).group_by(func.date(models.Vote.created_at))\
          .all()
        
        # Convert to DailyVoteCount objects
        results = []
        for vote_date, vote_count, unique_voters in daily_counts:
            results.append(DailyVoteCount(
                date=vote_date.strftime('%Y-%m-%d'),
                vote_count=vote_count,
                unique_voters=unique_voters
            ))
        
        return results
    
    def _calculate_engagement_trend(self, daily_votes: List[DailyVoteCount]) -> str:
        """Calculate overall engagement trend from daily vote data."""
        if len(daily_votes) < 2:
            return "stable"
        
        # Simple trend calculation based on first and last few days
        first_half_avg = sum(day.vote_count for day in daily_votes[:len(daily_votes)//2]) / (len(daily_votes)//2)
        second_half_avg = sum(day.vote_count for day in daily_votes[len(daily_votes)//2:]) / (len(daily_votes) - len(daily_votes)//2)
        
        if second_half_avg > first_half_avg * 1.1:
            return "increasing"
        elif second_half_avg < first_half_avg * 0.9:
            return "decreasing"
        else:
            return "stable"
    
    def _get_popular_voting_times(self, user_id: int, start_date: datetime, end_date: datetime) -> List[str]:
        """Get most popular voting hours for user's polls."""
        # Query votes grouped by hour
        hourly_counts = self.db.query(
            func.extract('hour', models.Vote.created_at).label('hour'),
            func.count(models.Vote.id).label('vote_count')
        ).join(models.Option)\
         .join(models.Poll)\
         .filter(
             and_(
                 models.Poll.owner_id == user_id,
                 models.Vote.created_at >= start_date,
                 models.Vote.created_at <= end_date
             )
         ).group_by(func.extract('hour', models.Vote.created_at))\
          .order_by(desc('vote_count'))\
          .limit(3)\
          .all()
        
        return [f"{int(hour):02d}:00" for hour, _ in hourly_counts]
    
    def _calculate_cutoff_date(self, timeframe: str) -> datetime:
        """Calculate cutoff date for timeframe-based queries."""
        now = datetime.now(UTC)
        
        if timeframe == "day":
            return now - timedelta(days=1)
        elif timeframe == "week":
            return now - timedelta(days=7)
        elif timeframe == "month":
            return now - timedelta(days=30)
        elif timeframe == "year":
            return now - timedelta(days=365)
        elif timeframe == "all":
            return datetime.min.replace(tzinfo=UTC)
        else:
            raise ValueError(f"Invalid timeframe: {timeframe}")