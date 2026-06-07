from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="AI Code Review Agent",
    description="Automated PR reviews powered by a fine-tuned LLM",
    version="1.0.0",
    docs_url="/docs",        # Swagger UI at /docs
    redoc_url="/redoc",
)

# Allow Next.js frontend to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# All routes live under /api/v1
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def health_check():
    return {
        "status": "online",
        "env": settings.app_env,
        "version": "1.0.0"
    }