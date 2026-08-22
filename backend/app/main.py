from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings
from contextlib import asynccontextmanager
from app.models.database import engine, Base, SessionLocal
from app.models.incident import Incident
from app.models.route_segment import PersistentRouteSegment
from app.models.washroom import Washroom, WashroomFeedback

Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Seed Washrooms
    db = SessionLocal()
    if db.query(Washroom).count() == 0:
        db.add_all([
            Washroom(name="Public Washroom - CP", address="Connaught Place, New Delhi", latitude=28.6304, longitude=77.2177),
            Washroom(name="Metro Station Washroom", address="Rajiv Chowk", latitude=28.6328, longitude=77.2197),
            Washroom(name="Market Sulabh", address="Janpath Market", latitude=28.6250, longitude=77.2185)
        ])
        db.commit()
    db.close()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8081",
        "http://127.0.0.1:8081",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message": "Welcome to SAKHI Backend Prototype"}

