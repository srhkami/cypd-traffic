from fastapi import APIRouter

from src.api.deps import ok
from src.api.schemas import AuthStatus
from src.utils.auth import cookie_store

router = APIRouter(prefix="/api/auth", tags=["認證"])


@router.get("/status")
def auth_status():
    """檢查目前的認證狀態"""
    status = AuthStatus(
        authenticated=cookie_store.is_authenticated(),
        last_auth_time=cookie_store.get_last_auth_time(),
    )
    return ok("取得認證狀態", data=status.model_dump())


@router.post("/logout")
def logout():
    """清除認證狀態"""
    cookie_store.clear()
    return ok("已登出")
