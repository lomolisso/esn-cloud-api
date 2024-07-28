from fastapi import FastAPI
from app.api.routes.application import application_router
from app.api.routes.gateway import gateway_router
from app.core.config import SECRET_KEY, ORIGINS
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
app.include_router(application_router, prefix="/api/v1")
app.include_router(gateway_router, prefix="/api/v1")
