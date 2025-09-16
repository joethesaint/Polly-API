# Polly-API Development Rules

## 🎯 AI Development Guidelines

These rules define the high-level patterns and principles that AI should follow when implementing features in the Polly-API project.

---

## Rule 1: Follow Existing Architecture Patterns

**Pattern**: Maintain consistency with the established FastAPI project structure

### Guidelines:
- **Route Organization**: Place new routes in dedicated modules (e.g., `api/analytics/routes.py`)
- **Dependency Injection**: Use FastAPI's `Depends()` for database sessions and authentication
- **Model Structure**: Follow SQLAlchemy ORM patterns established in `api/models.py`
- **Schema Validation**: Use Pydantic models for request/response validation in dedicated schema files
- **Error Handling**: Use FastAPI's `HTTPException` with appropriate status codes

### Example:
```python
# ✅ Good - Follows existing pattern
@router.get("/analytics/overview", response_model=AnalyticsOverview)
def get_analytics_overview(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return analytics_service.get_overview(db, current_user.id)

# ❌ Bad - Breaks established patterns
def analytics_overview(request):
    # Direct database access, no validation
```

---

## Rule 2: Implement Security-First Design

**Pattern**: Every endpoint must enforce proper authentication and authorization

### Guidelines:
- **Authentication**: All protected endpoints must use `get_current_user` dependency
- **Authorization**: Verify user ownership before accessing user-specific data
- **Data Privacy**: Never expose sensitive user information in analytics aggregations
- **Input Validation**: Validate and sanitize all user inputs using Pydantic schemas
- **Rate Limiting**: Consider rate limiting for resource-intensive analytics endpoints

### Example:
```python
# ✅ Good - Security-first approach
def get_poll_analytics(
    poll_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Verify ownership before proceeding
    poll = verify_poll_ownership(poll_id, current_user, db)
    return calculate_analytics(poll)

# ❌ Bad - No authorization check
def get_poll_analytics(poll_id: int, db: Session = Depends(get_db)):
    # Anyone can access any poll's analytics
```

---

## Rule 3: Optimize for Performance and Scalability

**Pattern**: Design with performance in mind from the start

### Guidelines:
- **Database Queries**: Use efficient SQLAlchemy queries with proper joins and indexing
- **Caching Strategy**: Implement caching for expensive calculations (Redis recommended)
- **Pagination**: Always paginate large result sets
- **Lazy Loading**: Use appropriate SQLAlchemy loading strategies
- **Async Operations**: Consider async/await for I/O-bound operations

### Example:
```python
# ✅ Good - Optimized query with caching
@lru_cache(maxsize=100)
def get_vote_distribution(db: Session, poll_id: int) -> Dict[str, int]:
    return db.query(
        Option.text,
        func.count(Vote.id).label('count')
    ).join(Vote).filter(Option.poll_id == poll_id)\
     .group_by(Option.id).all()

# ❌ Bad - N+1 query problem
def get_vote_distribution(db: Session, poll_id: int):
    options = db.query(Option).filter(Option.poll_id == poll_id).all()
    return {opt.text: len(opt.votes) for opt in options}  # N+1 queries
```

---

## Rule 4: Maintain Clean Code and Documentation

**Pattern**: Write self-documenting code with clear separation of concerns

### Guidelines:
- **Service Layer**: Separate business logic into service classes
- **Single Responsibility**: Each function should have one clear purpose
- **Type Hints**: Use comprehensive type annotations
- **Docstrings**: Document all public functions and classes
- **Error Messages**: Provide clear, actionable error messages

### Example:
```python
# ✅ Good - Clean, documented service method
class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_engagement_rate(self, poll_id: int) -> float:
        """
        Calculate engagement rate as (total_votes / poll_views) * 100.
        
        Args:
            poll_id: The ID of the poll to analyze
            
        Returns:
            Engagement rate as a percentage (0-100)
            
        Raises:
            ValueError: If poll not found or has no views
        """
        poll = self._get_poll_or_raise(poll_id)
        if poll.view_count == 0:
            return 0.0
        return (poll.total_votes / poll.view_count) * 100

# ❌ Bad - Unclear, undocumented function
def calc_rate(pid):
    p = db.query(Poll).get(pid)
    return p.votes / p.views * 100  # What if views is 0?
```

---

## Rule 5: Test-Driven Development Approach

**Pattern**: Write testable code and include comprehensive tests

### Guidelines:
- **Unit Tests**: Test individual functions with mock data
- **Integration Tests**: Test API endpoints with test database
- **Test Coverage**: Aim for >80% test coverage on new features
- **Mock External Dependencies**: Use pytest fixtures for database and auth
- **Edge Cases**: Test error conditions and boundary cases

### Example:
```python
# ✅ Good - Testable service method
class AnalyticsService:
    def get_popular_polls(self, limit: int = 10, timeframe: str = "week") -> List[Poll]:
        cutoff_date = self._calculate_cutoff_date(timeframe)
        return self.db.query(Poll)\
            .filter(Poll.created_at >= cutoff_date)\
            .order_by(Poll.vote_count.desc())\
            .limit(limit).all()
    
    def _calculate_cutoff_date(self, timeframe: str) -> datetime:
        """Helper method that can be easily tested"""
        if timeframe == "week":
            return datetime.now(UTC) - timedelta(days=7)
        elif timeframe == "month":
            return datetime.now(UTC) - timedelta(days=30)
        else:
            raise ValueError(f"Invalid timeframe: {timeframe}")

# Test for the above
def test_calculate_cutoff_date():
    service = AnalyticsService(mock_db)
    cutoff = service._calculate_cutoff_date("week")
    assert cutoff < datetime.now(UTC)
    assert cutoff > datetime.now(UTC) - timedelta(days=8)
```

---

## 📋 Implementation Checklist

When implementing the Poll Analytics Dashboard, ensure:

- [ ] New routes follow existing FastAPI patterns
- [ ] All endpoints have proper authentication/authorization
- [ ] Database queries are optimized and indexed
- [ ] Business logic is separated into service classes
- [ ] Comprehensive type hints and docstrings are included
- [ ] Unit and integration tests are written
- [ ] Error handling covers edge cases
- [ ] Caching is implemented for expensive operations
- [ ] Security considerations are addressed
- [ ] Performance implications are considered

---

## 🔄 Code Review Standards

Before committing, verify:

1. **Functionality**: Does the code work as intended?
2. **Security**: Are there any security vulnerabilities?
3. **Performance**: Will this scale with increased load?
4. **Maintainability**: Is the code easy to understand and modify?
5. **Testing**: Are there adequate tests covering the functionality?

---

*These rules ensure consistent, secure, and maintainable code throughout the Polly-API project.*