from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models
from config import CORS_ORIGINS
from database import Base, engine
from routers import auth, opportunities, registrations


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"status": "ok"}


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(opportunities.router, prefix="/opportunities", tags=["opportunities"])
app.include_router(registrations.router, prefix="/registrations", tags=["registrations"])
