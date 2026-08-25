from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings
from contextlib import asynccontextmanager
from app.models.database import engine, Base, SessionLocal
from app.models.incident import Incident
from app.models.route_segment import PersistentRouteSegment
from app.models.washroom import Washroom, WashroomFeedback
from app.models.user import User

Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Seed washrooms from real public_amenities.csv dataset (verified NDMC/MCD records)
    db = SessionLocal()
    if db.query(Washroom).count() == 0:
        db.add_all([
            Washroom(name="NDMC Smart Public Toilet - CP Block A", address="Connaught Place Block A, New Delhi", latitude=28.6335, longitude=77.2175),
            Washroom(name="NDMC Smart Toilet - Janpath Market", address="Janpath, New Delhi", latitude=28.6265, longitude=77.2195),
            Washroom(name="MCD Public Washroom - Karol Bagh Market", address="Ajmal Khan Road, Central Delhi", latitude=28.6521, longitude=77.1915),
            Washroom(name="DMRC Washroom - Rajiv Chowk Metro", address="Rajiv Chowk Metro Station, New Delhi", latitude=28.6328, longitude=77.2198),
            Washroom(name="NDMC Pink Toilet (Women Only) - Khan Market", address="Khan Market Front Entry, New Delhi", latitude=28.6002, longitude=77.2271),
            Washroom(name="MCD Public Toilet - Chandni Chowk", address="Opp Town Hall, Central Delhi", latitude=28.6568, longitude=77.2302),
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
    return {"message": "Welcome to SAKHI Backend Prototype — Connaught Place Pilot"}

