import threading

from fastapi import APIRouter

from src.api.deps import ok, fail
from src.api.schemas import ScrapeRequest
from src.api import tasks
from src.utils.auth import cookie_store
from src.utils.log import log

router = APIRouter(prefix="/api/tasks/scrape", tags=["爬取任務"])


@router.post("")
def start_scrape(body: ScrapeRequest):
    """
    啟動爬取案件的背景任務
    若 handle_mode=True 需提供 undertaker_id
    """
    headers = cookie_store.get_headers()
    if not headers:
        return fail("尚未認證，請先登入內網")

    task = tasks.create_task("scrape" if not body.handle_mode else "assign")

    def _run() -> None:
        from src.features.get import scrape_cases
        from src.models.undertaker import get_undertakers

        undertaker = None
        if body.handle_mode and body.undertaker_id is not None:
            undertakers = get_undertakers()
            undertaker = undertakers.get(body.undertaker_id)
            if not undertaker:
                tasks.update_task(
                    task.task_id,
                    status=tasks.TaskStatus.FAILED,
                    message="找不到指定的承辦人",
                )
                return

        tasks.update_task(
            task.task_id, status=tasks.TaskStatus.RUNNING, message="開始爬取案件"
        )

        try:
            results = scrape_cases(
                headers=headers,
                handle_mode=body.handle_mode,
                undertaker=undertaker,
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
                message=f"爬取完成，共處理 {len(results)} 筆",
            )
        except Exception as e:
            log().error(f"爬取任務失敗：{e}", exc_info=True)
            tasks.update_task(
                task.task_id, status=tasks.TaskStatus.FAILED, message=str(e)
            )

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return ok("爬取任務已啟動", data={"task_id": task.task_id})
