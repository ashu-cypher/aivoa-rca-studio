from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.db.session import Base, engine

# Import models so create_all sees every table.
import app.models.models  # noqa: F401

app = FastAPI(title="AIVOA RCA Studio API", description="AI-powered Root Cause Analysis for API manufacturing. Local demo without production access controls; reviewer identity is NOT authenticated.", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


app.include_router(router, prefix="/api")


@app.get("/")
def root():
    return {"app": "AIVOA RCA Studio", "docs": "/docs", "health": "/api/health"}
