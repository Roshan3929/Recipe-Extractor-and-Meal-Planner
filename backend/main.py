# FastAPI app entry point
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import models
from routes.recipes import router as recipes_router
from routes.meal_plan import router as meal_plan_router
from config import settings
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

logger.info(f"🚀 Initializing Recipe Extractor API - Environment: {settings.app_env}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

logger.info(f"✅ CORS configured for frontend: {settings.frontend_url}")

models.Base.metadata.create_all(bind=engine)
logger.info("✅ Database tables initialized")

app.include_router(recipes_router)
app.include_router(meal_plan_router)
logger.info("✅ API routers registered")

@app.get("/health")
def health():
    logger.info("🏥 Health check requested")
    return {"status": "ok", "env": settings.app_env}