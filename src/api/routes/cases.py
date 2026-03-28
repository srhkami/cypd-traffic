import json

from fastapi import APIRouter

from src.api.deps import ok, fail
from src.api.schemas import CaseOut, ReplyFieldsUpdate
from src.utils import db

router = APIRouter(prefix="/api/cases", tags=["案件"])


@router.get("")
def get_cases(status: str | None = None):
    """
    取得案件列表
    :param status: 篩選條件：未結案 / 已結案 / 未下載 / None (全部)
    """
    rows = db.get_cases_by_status(status)
    cases = [_row_to_case(row) for row in rows]
    return ok(f"取得 {len(cases)} 筆案件", data=cases)


@router.get("/{number}")
def get_case(number: str):
    """取得單一案件"""
    row = db.get_case_by_number(number)
    if row is None:
        return fail(f"找不到案號 {number}")
    return ok("取得案件成功", data=_row_to_case(row))


@router.patch("/{number}/reply-fields")
def update_reply_fields(number: str, body: ReplyFieldsUpdate):
    """更新案件回填欄位（input_code, fine, reject_answer）"""
    count = db.batch_update_reply_fields(
        number, body.input_code, body.fine, body.reject_answer
    )
    if count == 0:
        return fail(f"找不到案號 {number}，未更新")
    return ok(f"案號 {number} 回填欄位已更新")


def _row_to_case(row) -> dict:
    """將 sqlite3.Row 轉為 CaseOut 字典"""
    return CaseOut(
        number=row["number"],
        car=row["car"],
        detail_url=row["detail_url"],
        place=row["place"],
        content=row["content"],
        sender=row["sender"],
        year_roc=row["year_roc"],
        month=row["month"],
        day=row["day"],
        hour=row["hour"],
        minute=row["minute"],
        files_json=row["files_json"],
        undertaker=row["undertaker"],
        status=row["status"],
        input_code=row["input_code"],
        fine=row["fine"],
        reject_answer=row["reject_answer"],
        download_status=row["download_status"],
    ).model_dump()
