from fastapi import FastAPI
from api.database import Base, engine
from api import models
from api.routes import router
from api.analytics.routes import router as analytics_router

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Polly API", description="A polling application with analytics")
app.include_router(router)
app.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
