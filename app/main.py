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
import traceback

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
        
        with engine.begin() as conn:
            # Run Migrations (Add columns if missing)
            try:
                conn.execute(text("ALTER TABLE doctors ADD COLUMN IF NOT EXISTS lat FLOAT"))
                conn.execute(text("ALTER TABLE doctors ADD COLUMN IF NOT EXISTS lon FLOAT"))
            except Exception: pass

            # Seed default groups
            group_count = conn.execute(text("SELECT COUNT(*) FROM community_groups")).scalar()
            if group_count == 0:
                defaults = [
                    ("Early Detection", "early-detection", "Share and learn about early detection", "Search"),
                    ("Treatment Support", "treatment-support", "Support through treatment", "HeartHandshake"),
                    ("Family & Caregivers", "family-caregivers", "Loved ones support", "Users"),
                ]
                for name, slug, desc, icon in defaults:
                    conn.execute(text(
                        "INSERT INTO community_groups (name, slug, description, icon, is_private, created_at) "
                        "VALUES (:name, :slug, :desc, :icon, FALSE, NOW())"
                    ), {"name": name, "slug": slug, "desc": desc, "icon": icon})

            # Seed Doctors
            doc_count = conn.execute(text("SELECT COUNT(*) FROM doctors")).scalar()
            if doc_count == 0:
                conn.execute(text(
                    "INSERT INTO doctors (name, specialty, location, rating, experience, phone, is_verified, consultation_fee, languages, qualifications, bio, hospital_name, lat, lon) "
                    "VALUES ('Dr. Sarah Chen', 'Dermatological Oncology', 'London', 4.9, '12 years', '+44-20-1234-5678', TRUE, 200.0, 'English', 'MD, FRCP', 'Melanoma specialist.', 'London Skin Institute', 51.5074, -0.1278)"
                ))

            # Seed a welcome post
            post_count = conn.execute(text("SELECT COUNT(*) FROM posts")).scalar()
            if post_count == 0:
                # Find the first user
                user_id = conn.execute(text("SELECT id FROM users LIMIT 1")).scalar()
                if user_id:
                    conn.execute(text(
                        "INSERT INTO posts (title, content, category, user_id, created_at) "
                        "VALUES ('Welcome to OncoAI!', 'This is a safe space for skin health awareness.', 'General', :uid, NOW())"
                    ), {"uid": user_id})
            
            logger.info("Database initialization complete.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        traceback.print_exc()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(f"REQUEST: {request.method} {request.url.path} - {response.status_code} ({process_time:.2f}ms)")
        return response
    except Exception as e:
        logger.error(f"CRITICAL ERROR during {request.method} {request.url.path}: {e}")
        traceback.print_exc()
        # Return the error message to the app so we can see it
        return JSONResponse(
            status_code=500, 
            content={"detail": f"Server Error: {type(e).__name__}: {str(e)}"}
        )

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
