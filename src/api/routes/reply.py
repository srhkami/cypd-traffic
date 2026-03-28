import threading

from fastapi import APIRouter

from src.api.deps import ok, fail
from src.api.schemas import ReplyRequest
from src.api import tasks
from src.utils.auth import cookie_store
from src.utils.log import log

router = APIRouter(prefix="/api/tasks/reply", tags=["回覆任務"])


@router.post("")
def start_reply(body: ReplyRequest):
    """啟動批次回覆案件的背景任務"""
    headers = cookie_store.get_headers()
    if not headers:
        return fail("尚未認證，請先登入內網")

    task = tasks.create_task("reply")

    def _run() -> None:
        from src.features.reply import reply_cases

        tasks.update_task(
            task.task_id, status=tasks.TaskStatus.RUNNING, message="開始回覆案件"
        )

        try:
            results = reply_cases(
                headers=headers,
                station_mode=body.station_mode,
                re_assign=body.re_assign,
                on_progress=lambda cur, tot, msg: tasks.update_task(
                    task.task_id, current=cur, total=tot, message=msg
                ),
                is_cancelled=lambda: tasks.is_cancelled(task.task_id),
            )
            for r in results:
                tasks.update_task(task.task_id, result=r)
            tasks.update_task(
                task.task_id,
                status=tasks.TaskStatus.COMPLETED,
                message=f"回覆完成，共處理 {len(results)} 筆",
            )
        except Exception as e:
            log().error(f"回覆任務失敗：{e}", exc_info=True)
            tasks.update_task(
                task.task_id, status=tasks.TaskStatus.FAILED, message=str(e)
            )

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return ok("回覆任務已啟動", data={"task_id": task.task_id})
