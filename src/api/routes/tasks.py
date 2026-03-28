from fastapi import APIRouter

from src.api.deps import ok, fail
from src.api import tasks

router = APIRouter(prefix="/api/tasks", tags=["任務管理"])


@router.get("")
def list_all_tasks():
    """列出所有背景任務"""
    all_tasks = tasks.list_tasks()
    data = [t.model_dump() for t in all_tasks]
    return ok(f"共 {len(data)} 個任務", data=data)


@router.get("/{task_id}")
def get_task_status(task_id: str):
    """查詢單一任務進度"""
    task = tasks.get_task(task_id)
    if task is None:
        return fail(f"找不到任務 {task_id}")
    return ok("取得任務狀態", data=task.model_dump())


@router.delete("/{task_id}")
def cancel_task(task_id: str):
    """取消任務"""
    success = tasks.cancel_task(task_id)
    if not success:
        return fail(f"無法取消任務 {task_id}（不存在或已完成）")
    return ok(f"任務 {task_id} 已取消")
