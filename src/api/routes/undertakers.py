from fastapi import APIRouter

from src.api.deps import ok, fail
from src.api.schemas import UndertakerOut, UndertakerCreate
from src.models.undertaker import get_undertakers
from src.utils import db

router = APIRouter(prefix="/api/undertakers", tags=["承辦人"])


@router.get("")
def list_undertakers():
    """取得全部承辦人"""
    undertakers = get_undertakers()
    data = [
        UndertakerOut(
            station_id=sid, unit=u.unit, name=u.name, code=u.code
        ).model_dump()
        for sid, u in undertakers.items()
    ]
    return ok(f"取得 {len(data)} 位承辦人", data=data)


@router.post("")
def create_or_update_undertaker(body: UndertakerCreate):
    """新增或更新承辦人"""
    db.upsert_undertaker(body.station_id, body.unit, body.name, body.code)
    return ok(f"已儲存承辦人：{body.unit} - {body.name}")


@router.delete("/{station_id}")
def remove_undertaker(station_id: int):
    """刪除指定代號的承辦人"""
    count = db.delete_undertaker(station_id)
    if count == 0:
        return fail(f"找不到代號 {station_id} 的承辦人")
    return ok(f"已刪除代號 {station_id} 的承辦人")
