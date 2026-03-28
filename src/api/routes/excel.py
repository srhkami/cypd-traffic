import os

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse

from src.api.deps import ok, fail
from src.api.schemas import ExportRequest
from src.utils.excel_io import (
    export_cases_core,
    import_reply_fields_core,
    list_importable_files,
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


@router.get("/files")
def list_excel_files():
    """列出可匯入的 Excel 檔案"""
    files = list_importable_files()
    return ok(f"找到 {len(files)} 個檔案", data=files)


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
