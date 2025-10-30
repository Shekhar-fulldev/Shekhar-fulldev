from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from datetime import date
from typing import List
from .schemas import *
from .models import *
from .db.database import engine
from .routers import ac_routers, user_routers, general_routers
Base.metadata.create_all(bind=engine)
app = FastAPI(title="AC Maintenance System")

origins = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:8000",
        "https://yourfrontend.com",
]
app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,  # Allow cookies and authorization headers
        allow_methods=["*"],     # Allow all HTTP methods (GET, POST, PUT, etc.)
        allow_headers=["*"],     # Allow all headers
)
app.include_router(router=user_routers.router)
app.include_router(router=ac_routers.router)
app.include_router(router=general_routers.router)






from datetime import timedelta

from datetime import timedelta, date









