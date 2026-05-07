
from fastapi import APIRouter, FastAPI

from app.auth.api import router as auth_router
from app.contributions.api import router as contributions_router
from app.projects.api import router as projects_router


app = FastAPI()

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(contributions_router)

app.include_router(api_router)