from fastapi import APIRouter

from src.api.deps import ok, fail
from src.api.schemas import OptionOut, OptionUpdate
from src.models.options import get_option
from src.utils import db

router = APIRouter(prefix="/api/options", tags=["選項"])


@router.get("")
def get_options():
    """取得所有系統選項"""
    option = get_option()
    return ok("取得選項成功", data=option.model_dump())


@router.put("")
def update_options(body: OptionUpdate):
    """更新單一選項"""
    count = db.update_option(body.key, body.value)
    if count == 0:
        return fail(f"找不到選項 key：{body.key}")
    return ok(f"選項 {body.key} 已更新為 {body.value}")
