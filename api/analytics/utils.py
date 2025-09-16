"""Utility functions for analytics calculations and data processing."""

from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional, Tuple, Any
from functools import wraps
import hashlib
import json
from sqlalchemy.orm import Session
from sqlalchemy import func

from api import models


def cache_key_generator(*args, **kwargs) -> str:
    """
    Generate a cache key from function arguments.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        MD5 hash of the serialized arguments
    """
    # Create a string representation of all arguments
    key_data = {
        'args': [str(arg) for arg in args],
        'kwargs': {k: str(v) for k, v in sorted(kwargs.items())}
    }
    
    # Serialize and hash
    key_string = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_string.encode()).hexdigest()


def analytics_cache(ttl_seconds: int = 300):
    """
    Decorator for caching analytics results.
    
    Args:
        ttl_seconds: Time to live for cached results in seconds
        
    Note: This is a placeholder for Redis caching implementation.
    In production, this would integrate with Redis or similar cache.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"analytics:{func.__name__}:{cache_key_generator(*args, **kwargs)}"
            
            # In production, check Redis cache here
            # For now, just execute the function
            result = func(*args, **kwargs)
            
            # In production, store result in Redis with TTL
            return result
        
        return wrapper
    return decorator


class AnalyticsCalculator:
    """Helper class for complex analytics calculations."""
    
    @staticmethod
    def calculate_engagement_score(
        votes: int,
        views: int,
        unique_voters: int,
        poll_age_hours: float,
        option_count: int
    ) -> float:
        """
        Calculate a comprehensive engagement score for a poll.
        
        Args:
            votes: Total number of votes
            views: Total number of views
            unique_voters: Number of unique voters
            poll_age_hours: Age of poll in hours
            option_count: Number of options in the poll
            
        Returns:
            Engagement score between 0 and 100
        """
        if views == 0:
            return 0.0
        
        # Base engagement rate (votes/views)
        base_engagement = (votes / views) * 100
        
        # Voter diversity bonus (unique voters vs total votes)
        diversity_bonus = (unique_voters / votes) * 10 if votes > 0 else 0
        
        # Recency bonus (newer polls get slight boost)
        recency_bonus = max(0, 10 - (poll_age_hours / 24))  # Decay over 10 days
        
        # Option complexity factor (more options = higher engagement threshold)
        complexity_factor = min(1.2, 1 + (option_count - 2) * 0.1)
        
        # Calculate final score
        score = (base_engagement + diversity_bonus + recency_bonus) * complexity_factor
        
        return min(100.0, max(0.0, score))
    
    @staticmethod
    def calculate_trend_direction(values: List[float], window_size: int = 3) -> str:
        """
        Calculate trend direction from a series of values.
        
        Args:
            values: List of numeric values in chronological order
            window_size: Size of moving average window
            
        Returns:
            Trend direction: 'increasing', 'decreasing', or 'stable'
        """
        if len(values) < window_size * 2:
            return 'stable'
        
        # Calculate moving averages for first and last windows
        first_window = sum(values[:window_size]) / window_size
        last_window = sum(values[-window_size:]) / window_size
        
        # Determine trend with threshold
        threshold = 0.1  # 10% change threshold
        change_ratio = (last_window - first_window) / first_window if first_window > 0 else 0
        
        if change_ratio > threshold:
            return 'increasing'
        elif change_ratio < -threshold:
            return 'decreasing'
        else:
            return 'stable'
    
    @staticmethod
    def calculate_percentile_rank(value: float, dataset: List[float]) -> float:
        """
        Calculate percentile rank of a value within a dataset.
        
        Args:
            value: The value to rank
            dataset: List of values to compare against
            
        Returns:
            Percentile rank (0-100)
        """
        if not dataset:
            return 50.0
        
        sorted_data = sorted(dataset)
        count_below = sum(1 for x in sorted_data if x < value)
        count_equal = sum(1 for x in sorted_data if x == value)
        
        # Use average rank for tied values
        percentile = (count_below + count_equal / 2) / len(sorted_data) * 100
        
        return round(percentile, 2)


class TimeAnalyzer:
    """Helper class for time-based analytics."""
    
    @staticmethod
    def get_time_buckets(start_date: datetime, end_date: datetime, bucket_size: str = 'hour') -> List[datetime]:
        """
        Generate time buckets for temporal analysis.
        
        Args:
            start_date: Start of time range
            end_date: End of time range
            bucket_size: Size of buckets ('hour', 'day', 'week')
            
        Returns:
            List of datetime objects representing bucket boundaries
        """
        buckets = []
        current = start_date
        
        if bucket_size == 'hour':
            delta = timedelta(hours=1)
        elif bucket_size == 'day':
            delta = timedelta(days=1)
        elif bucket_size == 'week':
            delta = timedelta(weeks=1)
        else:
            raise ValueError(f"Invalid bucket size: {bucket_size}")
        
        while current <= end_date:
            buckets.append(current)
            current += delta
        
        return buckets
    
    @staticmethod
    def find_peak_activity_periods(
        timestamps: List[datetime],
        bucket_size: str = 'hour',
        top_n: int = 3
    ) -> List[Tuple[str, int]]:
        """
        Find periods with highest activity.
        
        Args:
            timestamps: List of activity timestamps
            bucket_size: Time bucket size for grouping
            top_n: Number of top periods to return
            
        Returns:
            List of (period_label, activity_count) tuples
        """
        if not timestamps:
            return []
        
        # Group timestamps by bucket
        bucket_counts = {}
        
        for ts in timestamps:
            if bucket_size == 'hour':
                bucket_key = f"{ts.hour:02d}:00"
            elif bucket_size == 'day':
                bucket_key = ts.strftime('%A')  # Day of week
            elif bucket_size == 'date':
                bucket_key = ts.strftime('%Y-%m-%d')
            else:
                bucket_key = str(ts)
            
            bucket_counts[bucket_key] = bucket_counts.get(bucket_key, 0) + 1
        
        # Sort by count and return top N
        sorted_periods = sorted(bucket_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_periods[:top_n]
    
    @staticmethod
    def calculate_activity_velocity(
        timestamps: List[datetime],
        window_hours: int = 24
    ) -> List[Tuple[datetime, float]]:
        """
        Calculate activity velocity over time windows.
        
        Args:
            timestamps: List of activity timestamps
            window_hours: Size of sliding window in hours
            
        Returns:
            List of (window_start, velocity) tuples
        """
        if not timestamps:
            return []
        
        sorted_timestamps = sorted(timestamps)
        window_delta = timedelta(hours=window_hours)
        velocities = []
        
        # Slide window through timestamps
        start_time = sorted_timestamps[0]
        end_time = sorted_timestamps[-1]
        
        current_time = start_time
        while current_time <= end_time:
            window_end = current_time + window_delta
            
            # Count activities in current window
            count = sum(
                1 for ts in sorted_timestamps
                if current_time <= ts < window_end
            )
            
            # Calculate velocity (activities per hour)
            velocity = count / window_hours
            velocities.append((current_time, velocity))
            
            # Move window forward by 1 hour
            current_time += timedelta(hours=1)
        
        return velocities


class DataAggregator:
    """Helper class for data aggregation operations."""
    
    @staticmethod
    def aggregate_by_time_period(
        db: Session,
        model_class,
        date_column,
        period: str = 'day',
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        filters: Optional[Dict] = None
    ) -> List[Tuple[str, int]]:
        """
        Aggregate data by time period.
        
        Args:
            db: Database session
            model_class: SQLAlchemy model class
            date_column: Column to group by
            period: Aggregation period ('hour', 'day', 'week', 'month')
            start_date: Start of date range
            end_date: End of date range
            filters: Additional filters to apply
            
        Returns:
            List of (period_label, count) tuples
        """
        query = db.query(model_class)
        
        # Apply date range filters
        if start_date:
            query = query.filter(date_column >= start_date)
        if end_date:
            query = query.filter(date_column <= end_date)
        
        # Apply additional filters
        if filters:
            for column, value in filters.items():
                query = query.filter(getattr(model_class, column) == value)
        
        # Group by time period
        if period == 'hour':
            time_group = func.date_trunc('hour', date_column)
            format_str = '%Y-%m-%d %H:00'
        elif period == 'day':
            time_group = func.date_trunc('day', date_column)
            format_str = '%Y-%m-%d'
        elif period == 'week':
            time_group = func.date_trunc('week', date_column)
            format_str = '%Y-W%U'
        elif period == 'month':
            time_group = func.date_trunc('month', date_column)
            format_str = '%Y-%m'
        else:
            raise ValueError(f"Invalid period: {period}")
        
        results = query.with_entities(
            time_group.label('period'),
            func.count().label('count')
        ).group_by('period').order_by('period').all()
        
        # Format results
        formatted_results = []
        for period_dt, count in results:
            if isinstance(period_dt, datetime):
                period_label = period_dt.strftime(format_str)
            else:
                period_label = str(period_dt)
            formatted_results.append((period_label, count))
        
        return formatted_results
    
    @staticmethod
    def calculate_moving_average(values: List[float], window_size: int) -> List[float]:
        """
        Calculate moving average of values.
        
        Args:
            values: List of numeric values
            window_size: Size of moving window
            
        Returns:
            List of moving averages
        """
        if len(values) < window_size:
            return values
        
        moving_averages = []
        for i in range(len(values) - window_size + 1):
            window = values[i:i + window_size]
            avg = sum(window) / window_size
            moving_averages.append(avg)
        
        return moving_averages
    
    @staticmethod
    def detect_anomalies(
        values: List[float],
        threshold_std: float = 2.0
    ) -> List[Tuple[int, float]]:
        """
        Detect anomalous values using standard deviation.
        
        Args:
            values: List of numeric values
            threshold_std: Number of standard deviations for anomaly threshold
            
        Returns:
            List of (index, value) tuples for anomalous values
        """
        if len(values) < 3:
            return []
        
        # Calculate mean and standard deviation
        mean_val = sum(values) / len(values)
        variance = sum((x - mean_val) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        
        # Find anomalies
        anomalies = []
        threshold = threshold_std * std_dev
        
        for i, value in enumerate(values):
            if abs(value - mean_val) > threshold:
                anomalies.append((i, value))
        
        return anomalies


# Utility functions for common analytics operations

def format_percentage(value: float, decimal_places: int = 1) -> str:
    """Format a decimal as a percentage string."""
    return f"{value:.{decimal_places}f}%"


def format_large_number(value: int) -> str:
    """Format large numbers with appropriate suffixes (K, M, B)."""
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    elif value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    elif value >= 1_000:
        return f"{value / 1_000:.1f}K"
    else:
        return str(value)


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero."""
    return numerator / denominator if denominator != 0 else default


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between minimum and maximum bounds."""
    return max(min_val, min(max_val, value))