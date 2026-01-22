from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.members import router as members_router
from app.api.routes.pk import router as pk_router
from app.api.routes.problems import router as problems_router
from app.api.routes.contests import router as contests_router
from app.api.routes.submissions import router as submissions_router
from app.api.routes.external_contests import router as external_contests_router
from app.api.routes.ai_interviews import router as ai_interviews_router
from app.api.routes.teams import router as teams_router
from app.api.routes.me import router as me_router
from app.api.routes.resume import router as resume_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(users_router, tags=["users"])
api_router.include_router(members_router, tags=["members"])
api_router.include_router(pk_router, tags=["pk"])
api_router.include_router(problems_router, tags=["problems"])
api_router.include_router(contests_router, tags=["contests"])
api_router.include_router(submissions_router, tags=["submissions"])
api_router.include_router(teams_router, tags=["teams"])
api_router.include_router(me_router, tags=["me"])
api_router.include_router(resume_router, tags=["resume"])
api_router.include_router(external_contests_router, tags=["external_contests"])
api_router.include_router(ai_interviews_router, tags=["ai_interviews"])

