from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import auth, scan, doctors, community, assistant, files, appointments, moderation, groups, notifications, users, checkins, messaging
from app.db.session import engine, Base
from app import models
from fastapi.responses import JSONResponse
from sqlalchemy import text
import time
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.PROJECT_NAME, description="Educational Skin Health Awareness Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up and initializing database...")
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        with engine.connect() as conn:
            # Run Migrations
            doctor_cols = [
                ("lat", "FLOAT"), ("lon", "FLOAT"), ("bio", "TEXT"),
                ("qualifications", "VARCHAR"), ("languages", "VARCHAR"),
                ("consultation_fee", "FLOAT"), ("is_verified", "BOOLEAN"),
                ("hospital_name", "VARCHAR"), ("google_place_id", "VARCHAR"),
            ]
            for col_name, col_type in doctor_cols:
                try:
                    conn.execute(text(f"ALTER TABLE doctors ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
                except Exception: pass

            post_cols = [
                ("image_url", "VARCHAR"), ("is_flagged", "BOOLEAN DEFAULT FALSE"),
                ("flag_reason", "TEXT"), ("flagged_by", "INTEGER"),
                ("is_hidden", "BOOLEAN DEFAULT FALSE"), ("pinned", "BOOLEAN DEFAULT FALSE"),
                ("group_id", "INTEGER"), ("is_anonymous", "BOOLEAN DEFAULT FALSE"),
            ]
            for col_name, col_type in post_cols:
                try:
                    conn.execute(text(f"ALTER TABLE posts ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
                except Exception: pass

            # Seed default groups
            existing = conn.execute(text("SELECT COUNT(*) FROM community_groups")).scalar()
            if existing == 0:
                defaults = [
                    ("Early Detection", "early-detection", "Share and learn about early detection strategies", "Search"),
                    ("Treatment Support", "treatment-support", "Support through treatment journeys", "HeartHandshake"),
                    ("Family & Caregivers", "family-caregivers", "A space for caregivers and loved ones", "Users"),
                    ("Recovery Journeys", "recovery-journeys", "Celebrate recovery milestones together", "Sparkles"),
                    ("Emotional Wellbeing", "emotional-wellbeing", "Mental and emotional health support", "Heart"),
                ]
                for name, slug, desc, icon in defaults:
                    conn.execute(text(
                        "INSERT INTO community_groups (name, slug, description, icon, is_private, created_at) "
                        "VALUES (:name, :slug, :desc, :icon, :private, NOW())"
                    ), {"name": name, "slug": slug, "desc": desc, "icon": icon, "private": False})
            
            conn.commit()
            logger.info("Database initialization complete.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    logger.info(f"REQUEST: {request.method} {request.url.path} - {response.status_code} ({process_time:.2f}ms)")
    return response

@app.get("/")
def read_root():
    return {"message": "Welcome to OncoAI API", "status": "online"}

API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=f"{API_PREFIX}/auth", tags=["auth"])
app.include_router(scan.router, prefix=f"{API_PREFIX}/scan", tags=["scan"])
app.include_router(doctors.router, prefix=f"{API_PREFIX}/doctors", tags=["doctors"])
app.include_router(community.router, prefix=f"{API_PREFIX}/community", tags=["community"])
app.include_router(assistant.router, prefix=f"{API_PREFIX}/assistant", tags=["assistant"])
app.include_router(files.router, prefix=f"{API_PREFIX}/files", tags=["files"])
app.include_router(appointments.router, prefix=f"{API_PREFIX}/appointments", tags=["appointments"])
app.include_router(moderation.router, prefix=f"{API_PREFIX}/moderation", tags=["moderation"])
app.include_router(groups.router, prefix=f"{API_PREFIX}/groups", tags=["groups"])
app.include_router(notifications.router, prefix=f"{API_PREFIX}/notifications", tags=["notifications"])
app.include_router(users.router, prefix=f"{API_PREFIX}/users", tags=["users"])
app.include_router(checkins.router, prefix=f"{API_PREFIX}/checkins", tags=["checkins"])
app.include_router(messaging.router, prefix=f"{API_PREFIX}/messaging", tags=["messaging"])

@app.get("/health")
def health_check():
    return {"status": "healthy"}
