from typing import Any

from pydantic import BaseModel


# ─────────────────── 統一回應格式 ───────────────────


class ApiResponse(BaseModel):
    """所有 API 回應的統一外層結構"""

    success: bool
    message: str
    data: Any = None


# ─────────────────── 案件相關 ───────────────────


class CaseOut(BaseModel):
    """案件回應模型（對外輸出用）"""

    number: str
    car: str
    detail_url: str
    place: str
    content: str
    sender: str
    year_roc: str
    month: str
    day: str
    hour: str
    minute: str
    files_json: str
    undertaker: str
    status: str
    input_code: int
    fine: str | None = None
    reject_answer: str | None = None


class ReplyFieldsUpdate(BaseModel):
    """更新回填欄位的請求模型"""

    input_code: int
    fine: str | None = None
    reject_answer: str | None = None


# ─────────────────── 法條相關 ───────────────────


class ArticleOut(BaseModel):
    """法條回應模型"""

    input_key: int
    code: int
    text: str


class ArticleCreate(BaseModel):
    """新增/更新法條的請求模型"""

    input_key: int
    code: int
    text: str


# ─────────────────── 承辦人相關 ───────────────────


class UndertakerOut(BaseModel):
    """承辦人回應模型"""

    station_id: int
    unit: str
    name: str
    code: int


class UndertakerCreate(BaseModel):
    """新增/更新承辦人的請求模型"""

    station_id: int
    unit: str
    name: str
    code: int


# ─────────────────── 選項相關 ───────────────────


class OptionOut(BaseModel):
    """系統選項回應模型"""

    check: bool
    car: bool
    article: bool
    text_y: str
    text_n: str
    download_limit: int


class OptionUpdate(BaseModel):
    """更新選項的請求模型"""

    key: str
    value: str


# ─────────────────── 認證相關 ───────────────────


class AuthStatus(BaseModel):
    """認證狀態回應"""

    authenticated: bool
    last_auth_time: str | None = None


# ─────────────────── 背景任務相關 ───────────────────


class TaskOut(BaseModel):
    """背景任務狀態回應"""

    task_id: str
    task_type: str
    status: str
    progress: int
    total: int
    current: int
    message: str
    created_at: str
    results: list[dict]


class ScrapeRequest(BaseModel):
    """啟動爬取任務的請求模型"""

    handle_mode: bool = False
    undertaker_id: int | None = None


class ReplyRequest(BaseModel):
    """啟動回覆任務的請求模型"""

    station_mode: bool = True
    re_assign: bool = False


class ExportRequest(BaseModel):
    """匯出 Excel 的請求模型"""

    status_filter: str | None = None
