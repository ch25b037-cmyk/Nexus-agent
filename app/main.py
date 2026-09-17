# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.services.schedulers import start_scheduler, scheduler

# Import our 7 clean, modular domain routers!
from app.api import auth, job, resume, shortlist, agent, briefing, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[*] Booting NEXUS engine: initializing scheduler...")
    start_scheduler(interval_hours=12)
    yield
    print("[*] Shutting down NEXUS engine...")
    if scheduler.running:
        scheduler.shutdown()


app = FastAPI(
    title="NEXUS — Career Intelligence Engine",
    description="Autonomous Career Intelligence Agent powered by pgvector, Groq, and Gemini.",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount all 7 domain routers!
app.include_router(auth.router)
app.include_router(job.router)
app.include_router(resume.router)
app.include_router(shortlist.router)
app.include_router(agent.router)
app.include_router(briefing.router)
app.include_router(admin.router)   


@app.get("/health", tags=["General"])
def health_check():
    return {"status": "healthy", "service": "NEXUS Core API (Modular Routers)"}