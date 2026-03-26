"""Central v1 router -- includes all sub-routers."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.agents import router as agents_router
from app.api.v1.transfers import router as transfers_router
from app.api.v1.corridors import router as corridors_router
from app.api.v1.investments import router as investments_router
from app.api.v1.compliance import router as compliance_router
from app.api.v1.matching import router as matching_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(agents_router)
api_v1_router.include_router(transfers_router)
api_v1_router.include_router(corridors_router)
api_v1_router.include_router(investments_router)
api_v1_router.include_router(compliance_router)
api_v1_router.include_router(matching_router)
