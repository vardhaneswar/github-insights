from fastapi import FastAPI
from src.routers.health import router as health_router
from src.routers.github import router as github_router
from src.routers.metrics import router as metrics_router
from src.routers.ai import router as ai_router
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI()

app.include_router(health_router)
app.include_router(github_router, prefix="/api/github")
app.include_router(metrics_router, prefix="/api/metrics")
app.include_router(ai_router, prefix="/api/ai")
# app = FastAPI()

# ----------------------------------------------------
# CORS FIX → allow frontend http://localhost:5173
# ----------------------------------------------------
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
