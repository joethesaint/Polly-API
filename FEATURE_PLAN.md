# Poll Analytics Dashboard - Architecture Plan

## 🎯 Feature Overview
**Selected Feature**: Poll Analytics Dashboard

A comprehensive analytics system that provides insights into poll performance, user engagement, and voting trends. This feature will help poll creators understand their audience and optimize their content.

## 📁 Folder Structure

```
api/
├── analytics/
│   ├── __init__.py
│   ├── routes.py          # Analytics API endpoints
│   ├── services.py        # Business logic for analytics calculations
│   ├── schemas.py         # Pydantic models for analytics responses
│   └── utils.py           # Helper functions for data aggregation
├── models.py              # (existing - may need extensions)
├── routes.py              # (existing - main routes)
└── ...
```

## 🔧 Function Signatures

### Analytics Routes (`api/analytics/routes.py`)
```python
@router.get("/analytics/overview", response_model=AnalyticsOverview)
def get_analytics_overview(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
) -> AnalyticsOverview:
    """Get overall analytics summary for the current user's polls"""

@router.get("/analytics/polls/{poll_id}", response_model=PollAnalytics)
def get_poll_analytics(
    poll_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
) -> PollAnalytics:
    """Get detailed analytics for a specific poll"""

@router.get("/analytics/trends", response_model=VotingTrends)
def get_voting_trends(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
) -> VotingTrends:
    """Get voting trends over specified time period"""

@router.get("/analytics/popular", response_model=List[PopularPoll])
def get_popular_polls(
    limit: int = 10,
    timeframe: str = "week",
    db: Session = Depends(get_db)
) -> List[PopularPoll]:
    """Get most popular polls (public endpoint)"""
```

### Analytics Services (`api/analytics/services.py`)
```python
class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_poll_engagement(self, poll_id: int) -> float:
        """Calculate engagement rate for a poll"""
    
    def get_vote_distribution(self, poll_id: int) -> Dict[str, int]:
        """Get vote count distribution across options"""
    
    def calculate_user_activity(self, user_id: int, days: int = 30) -> Dict:
        """Calculate user's polling activity metrics"""
    
    def get_trending_polls(self, timeframe: str = "week") -> List[Dict]:
        """Get polls with highest recent activity"""
    
    def calculate_poll_performance_score(self, poll_id: int) -> float:
        """Calculate overall performance score based on votes, engagement, time"""
```

### Analytics Schemas (`api/analytics/schemas.py`)
```python
class AnalyticsOverview(BaseModel):
    total_polls: int
    total_votes_received: int
    average_engagement_rate: float
    most_popular_poll: Optional[PollSummary]
    recent_activity: List[ActivityItem]

class PollAnalytics(BaseModel):
    poll_id: int
    poll_question: str
    total_votes: int
    engagement_rate: float
    vote_distribution: Dict[str, int]
    performance_score: float
    created_at: datetime
    peak_voting_time: Optional[datetime]

class VotingTrends(BaseModel):
    timeframe: str
    daily_votes: List[DailyVoteCount]
    popular_times: List[str]
    engagement_trend: str  # "increasing", "decreasing", "stable"

class PopularPoll(BaseModel):
    poll_id: int
    question: str
    vote_count: int
    engagement_rate: float
    created_at: datetime
```

## 🔒 Security Considerations

### Authentication & Authorization
- **User-specific analytics**: Users can only view analytics for their own polls
- **Public analytics**: Popular polls endpoint available without authentication
- **Rate limiting**: Implement rate limiting for analytics endpoints to prevent abuse
- **Data privacy**: Ensure no personal voting information is exposed in aggregated data

### Data Access Control
```python
# Security middleware for analytics routes
def verify_poll_ownership(poll_id: int, current_user: User, db: Session):
    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll or poll.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
```

## ⚡ Performance Considerations

### Database Optimization
- **Indexing**: Add indexes on frequently queried columns (created_at, poll_id, user_id)
- **Caching**: Implement Redis caching for expensive analytics calculations
- **Aggregation**: Pre-calculate common metrics and store in cache
- **Pagination**: Implement pagination for large result sets

### Query Optimization
```python
# Efficient vote counting with SQLAlchemy
def get_vote_counts_optimized(db: Session, poll_id: int):
    return db.query(
        Option.text,
        func.count(Vote.id).label('vote_count')
    ).join(Vote, Option.id == Vote.option_id)\
     .filter(Option.poll_id == poll_id)\
     .group_by(Option.id, Option.text)\
     .all()
```

### Caching Strategy
- **TTL**: 5 minutes for real-time data, 1 hour for historical trends
- **Cache keys**: `analytics:poll:{poll_id}`, `analytics:user:{user_id}:overview`
- **Invalidation**: Clear cache when new votes are cast

## 📊 Data Models Extensions

Potential additions to existing models:
```python
# Add to Poll model
class Poll(Base):
    # ... existing fields ...
    view_count = Column(Integer, default=0)  # Track poll views
    
# New analytics cache table
class AnalyticsCache(Base):
    __tablename__ = "analytics_cache"
    id = Column(Integer, primary_key=True)
    cache_key = Column(String, unique=True, index=True)
    data = Column(JSON)  # Store calculated analytics
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
```

## 🚀 Implementation Priority

1. **Phase 1**: Basic analytics routes and schemas
2. **Phase 2**: Analytics service layer with core calculations
3. **Phase 3**: Performance optimizations and caching
4. **Phase 4**: Advanced features (trends, predictions)

## 🧪 Testing Strategy

- **Unit tests**: Test analytics calculations with mock data
- **Integration tests**: Test API endpoints with real database
- **Performance tests**: Ensure analytics queries perform well with large datasets
- **Security tests**: Verify access control and data privacy

---

*This architecture provides a scalable foundation for poll analytics while maintaining security and performance standards.*