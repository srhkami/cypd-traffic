import os

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse

from src.api.deps import ok, fail
from src.api.schemas import ExportRequest
from src.utils import db
from src.utils.excel_io import (
    export_cases_core,
    import_reply_fields_core,
    get_data_dir,
)

router = APIRouter(prefix="/api/excel", tags=["Excel"])


@router.post("/export")
def export_excel(body: ExportRequest):
    """匯出案件至 Excel"""
    result = export_cases_core(body.status_filter)
    if "error" in result:
        return fail(result["error"])
    return ok(
        f"已匯出 {result['count']} 筆案件",
        data={"filename": result["filename"], "count": result["count"]},
    )


@router.get("/download/{filename}")
def download_excel(filename: str):
    """下載指定的 Excel 檔案"""
    filepath = os.path.join(get_data_dir(), filename)
    if not os.path.exists(filepath):
        return fail(f"找不到檔案：{filename}")
    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename,
    )


@router.post("/import")
async def import_excel(file: UploadFile = File(...)):
    """上傳 Excel 並匯入回填資料"""
    # 將上傳檔案暫存到 data/ 目錄
    data_dir = get_data_dir()
    temp_path = os.path.join(data_dir, f"upload_{file.filename}")

    try:
        contents = await file.read()
        with open(temp_path, "wb") as f:
            f.write(contents)

        result = import_reply_fields_core(temp_path)

        if "error" in result:
            return fail(result["error"])
        return ok(
            f"匯入完成：更新 {result['updated']} 筆，略過 {result['skipped']} 筆",
            data=result,
        )
    finally:
        # 清除暫存檔
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.get("/migrate/status")
def migration_status():
    """檢查是否有舊版 Excel 可遷移"""
    status = db.check_migration_available()
    return ok("取得遷移狀態", data=status)


@router.post("/migrate")
def run_migration():
    """執行舊版 Excel 遷移至 SQLite"""
    status = db.check_migration_available()
    if not status["available"]:
        return fail("找不到舊版 Excel 檔案（database.xlsx 或 setting.xlsx）")

    try:
        result = db.migrate_from_excel()
        parts = []
        if result["cases"]:
            parts.append(f"案件 {result['cases']} 筆")
        if result["articles"]:
            parts.append(f"法條 {result['articles']} 筆")
        if result["undertakers"]:
            parts.append(f"承辦人 {result['undertakers']} 筆")
        if result["options"]:
            parts.append("選項已更新")
        msg = "遷移完成：" + "、".join(parts) if parts else "遷移完成，但未匯入任何資料"
        return ok(msg, data=result)
    except Exception as e:
        return fail(f"遷移失敗：{str(e)}")
