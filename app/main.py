from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router as api_router
from app.core.config import settings
from app.services.db_service import init_db

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="AI Health Assistant API with RAG capabilities",
        version="2.0.0",
    )

    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.on_event("startup")
    async def startup_event():
        print("🚀 Starting up HealNet API...")
        init_db()

    @app.get("/")
    async def root():
        return {
            "message": "Welcome to HealNet API",
            "version": "2.0.0",
            "status": "online"
        }

    return app

app = create_app()
