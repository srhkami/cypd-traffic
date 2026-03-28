from fastapi import APIRouter

from src.api.deps import ok
from src.api.schemas import UndertakerOut
from src.models.undertaker import get_undertakers

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
