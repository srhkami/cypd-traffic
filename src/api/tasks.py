import uuid
from datetime import datetime
from enum import Enum
from threading import Lock

from pydantic import BaseModel


class TaskStatus(str, Enum):
    """背景任務狀態"""

    PENDING = "待處理"
    RUNNING = "執行中"
    COMPLETED = "已完成"
    FAILED = "失敗"
    CANCELLED = "已取消"


class TaskInfo(BaseModel):
    """背景任務的完整資訊"""

    task_id: str
    task_type: str  # scrape / assign / reply / download
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0  # 0~100
    total: int = 0  # 總筆數
    current: int = 0  # 已處理筆數
    message: str = ""  # 目前狀態描述
    created_at: str = ""
    results: list[dict] = []  # 每筆案件的處理結果


# ─────────────────── 全域任務儲存 ───────────────────

_tasks: dict[str, TaskInfo] = {}
_lock = Lock()


def create_task(task_type: str) -> TaskInfo:
    """建立新的背景任務並回傳"""
    task_id = uuid.uuid4().hex[:12]
    task = TaskInfo(
        task_id=task_id,
        task_type=task_type,
        created_at=datetime.now().isoformat(),
    )
    with _lock:
        _tasks[task_id] = task
    return task


def get_task(task_id: str) -> TaskInfo | None:
    """取得任務資訊"""
    with _lock:
        return _tasks.get(task_id)


def update_task(
    task_id: str,
    status: TaskStatus | None = None,
    progress: int | None = None,
    total: int | None = None,
    current: int | None = None,
    message: str | None = None,
    result: dict | None = None,
) -> None:
    """更新任務狀態"""
    with _lock:
        task = _tasks.get(task_id)
        if task is None:
            return
        if status is not None:
            task.status = status
        if total is not None:
            task.total = total
        if current is not None:
            task.current = current
        if progress is not None:
            task.progress = progress
        elif task.total > 0:
            task.progress = int(task.current / task.total * 100)
        if message is not None:
            task.message = message
        if result is not None:
            task.results.append(result)


def cancel_task(task_id: str) -> bool:
    """取消任務（僅標記，實際中止需任務自行檢查）"""
    with _lock:
        task = _tasks.get(task_id)
        if task is None:
            return False
        if task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
            task.status = TaskStatus.CANCELLED
            return True
        return False


def list_tasks() -> list[TaskInfo]:
    """列出所有任務"""
    with _lock:
        return list(_tasks.values())


def is_cancelled(task_id: str) -> bool:
    """檢查任務是否已被取消（供背景執行緒查詢）"""
    with _lock:
        task = _tasks.get(task_id)
        if task is None:
            return True
        return task.status == TaskStatus.CANCELLED
