from app.api.routes import api_router
from fastapi import FastAPI
from app.config import SECRET_KEY, ORIGINS
from app.database import Base, engine
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(api_router)

Base.metadata.create_all(bind=engine)