from fastapi import FastAPI
from src.routers.health import router as health_router
from src.routers.github import router as github_router
from src.routers.metrics import router as metrics_router
from src.routers.ai import router as ai_router


app = FastAPI()

app.include_router(health_router)
app.include_router(github_router, prefix="/api/github")
app.include_router(metrics_router, prefix="/api/metrics")
app.include_router(ai_router, prefix="/api/ai")
