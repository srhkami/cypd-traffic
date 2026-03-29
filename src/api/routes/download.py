import threading

from fastapi import APIRouter

from src.api.deps import ok
from src.api import tasks
from src.utils.log import log

router = APIRouter(prefix="/api/tasks/download", tags=["下載任務"])


@router.post("")
def start_download():
    """啟動批次下載附件的背景任務"""
    task = tasks.create_task("download")

    def _run() -> None:
        from src.features.download import download_all_cases

        tasks.update_task(
            task.task_id, status=tasks.TaskStatus.RUNNING, message="開始下載附件"
        )

        try:
            results = download_all_cases(
                on_progress=lambda cur, tot, msg: tasks.update_task(
                    task.task_id, current=cur, total=tot, message=msg
                ),
                on_result=lambda r: tasks.update_task(task.task_id, result=r),
                is_cancelled=lambda: tasks.is_cancelled(task.task_id),
            )
            tasks.update_task(
                task.task_id,
                status=tasks.TaskStatus.COMPLETED,
                message=f"下載完成，共處理 {len(results)} 筆",
            )
        except Exception as e:
            log().error(f"下載任務失敗：{e}", exc_info=True)
            tasks.update_task(
                task.task_id, status=tasks.TaskStatus.FAILED, message=str(e)
            )

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return ok("下載任務已啟動", data={"task_id": task.task_id})
