import os
import platform
import subprocess

from fastapi import APIRouter
from pydantic import BaseModel

from src.api.deps import ok, fail
from src.utils.log import log

router = APIRouter(prefix="/api/files", tags=["檔案管理"])

FILES_DIR = "files"


class FileOpenRequest(BaseModel):
    """開啟檔案的請求模型"""

    case_number: str
    car: str
    file_name: str


class FolderOpenRequest(BaseModel):
    """開啟資料夾的請求模型"""

    case_number: str
    car: str


@router.get("/{case_number}/{car}")
def list_case_files(case_number: str, car: str) -> dict:
    """
    列出指定案件資料夾內的檔案清單
    :param case_number: 案號
    :param car: 車號
    :return: 檔案名稱清單
    """
    folder = os.path.join(FILES_DIR, f"{case_number}_{car}")
    if not os.path.isdir(folder):
        return ok("資料夾尚未建立", data={"files": [], "exists": False})

    file_list = []
    for f in sorted(os.listdir(folder)):
        file_path = os.path.join(folder, f)
        if os.path.isfile(file_path):
            file_list.append(
                {
                    "name": f,
                    "size": os.path.getsize(file_path),
                }
            )

    return ok(f"共 {len(file_list)} 個檔案", data={"files": file_list, "exists": True})


@router.post("/open")
def open_file(body: FileOpenRequest) -> dict:
    """
    用系統預設程式打開指定檔案
    :param body: 包含案號、車號、檔案名稱
    :return: 操作結果
    """
    folder = os.path.join(FILES_DIR, f"{body.case_number}_{body.car}")
    file_path = os.path.join(folder, body.file_name)

    if not os.path.isfile(file_path):
        return fail(f"找不到檔案：{body.file_name}")

    abs_path = os.path.abspath(file_path)
    log().info(f"開啟檔案：{abs_path}")

    try:
        system = platform.system()
        if system == "Windows":
            os.startfile(abs_path)
        elif system == "Darwin":
            subprocess.Popen(["open", abs_path])
        else:
            subprocess.Popen(["xdg-open", abs_path])
        return ok(f"已開啟檔案：{body.file_name}")
    except Exception as e:
        log().error(f"開啟檔案失敗：{e}", exc_info=True)
        return fail(f"開啟檔案失敗：{str(e)}")


@router.post("/open-folder")
def open_folder(body: FolderOpenRequest) -> dict:
    """
    用系統檔案管理器打開案件資料夾
    :param body: 包含 case_number 和 car
    :return: 操作結果
    """
    folder = os.path.join(FILES_DIR, f"{body.case_number}_{body.car}")

    if not os.path.isdir(folder):
        return fail(f"資料夾不存在：{body.case_number}_{body.car}")

    abs_path = os.path.abspath(folder)
    log().info(f"開啟資料夾：{abs_path}")

    try:
        system = platform.system()
        if system == "Windows":
            os.startfile(abs_path)
        elif system == "Darwin":
            subprocess.Popen(["open", abs_path])
        else:
            subprocess.Popen(["xdg-open", abs_path])
        return ok(f"已開啟資料夾：{body.case_number}_{body.car}")
    except Exception as e:
        log().error(f"開啟資料夾失敗：{e}", exc_info=True)
        return fail(f"開啟資料夾失敗：{str(e)}")
