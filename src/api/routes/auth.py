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


@router.post("/login")
def trigger_login():
    """
    觸發 pywebview 開啟內網登入頁面
    實際登入流程由 main_gui.py 的 pywebview 視窗處理
    此端點僅回傳是否需要登入的狀態
    """
    if cookie_store.is_authenticated():
        return ok("已認證，無需重新登入")
    return ok("請透過應用程式視窗完成內網登入", data={"need_login": True})


@router.post("/logout")
def logout():
    """清除認證狀態"""
    cookie_store.clear()
    return ok("已登出")
