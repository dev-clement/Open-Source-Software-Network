
from fastapi import FastAPI

from app.auth.api import router as auth_router
from app.contributions.api import router as contributions_router
from app.projects.api import router as projects_router


app = FastAPI()

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(contributions_router)