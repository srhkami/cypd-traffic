from typing import Callable

from pydantic import BaseModel

from src.features.get import get_case_detail, assign_case_by_post
from src.models.article import get_articles, Article
from src.models.options import get_option, Option
from src.models.undertaker import get_undertakers
from src.utils.log import log
from src.models.case import CaseReply
from src.utils.webdriver import get_intranet_headers
from src.utils import db
import requests
import pprint


class ReplyPostPayload(BaseModel):
    """回覆案件 POST 請求的資料格式"""

    Memo: str
    Status: str
    IsEnd: str
    isReport: str
    MailboxTrafficCatalogRejectId: int
    MailboxTrafficArchiveTitle: str
    MailboxTrafficCatalogBackgroundId: int


class ReplyPostData:
    """回覆案件 Post 請求所需要的資料"""

    def __init__(
        self, case: CaseReply, option: Option, articles: dict[int, Article]
    ) -> None:
        self.case = case
        self.option = option
        self.articles = articles

    def post_data(self) -> ReplyPostPayload:
        reply_text = (
            "您於本縣警察局交通違規檢舉專區檢舉違規案件，經處理後茲答覆如下：\n"
        )

        if self.case.input == 100:
            log().debug("本案為不舉發")
            reply_text += self.case.reject_answer
            reply_text += self.option.text_n
        else:
            log().debug("本案為舉發")
            if self.option.car:
                reply_text += f"違規車號： {self.case.car}。\n"
            if self.option.article:
                reply_text += f"舉發法條： {self.articles[self.case.input].text} 。\n"
            reply_text += self.option.text_y

        payload = ReplyPostPayload(
            Memo=reply_text,
            Status="第一次回覆",
            IsEnd="是",
            isReport="否" if self.case.input == 100 else "是",
            MailboxTrafficCatalogRejectId=13,
            MailboxTrafficArchiveTitle=self.case.fine if self.case.input != 100 else "",
            MailboxTrafficCatalogBackgroundId=self.articles[self.case.input].code
            if self.case.input != 100
            else 53,
        )

        log().debug(payload)
        return payload


# ─────────────────── 核心邏輯（無 input() 互動） ───────────────────


def reply_cases(
    headers: dict,
    station_mode: bool = True,
    re_assign: bool = False,
    on_progress: Callable[[int, int, str], None] | None = None,
    is_cancelled: Callable[[], bool] | None = None,
) -> list[dict]:
    """
    回覆案件的核心邏輯（不含 CLI 互動）
    :param headers: 內網 HTTP 標頭
    :param station_mode: 是否為派出所模式
    :param re_assign: 是否重新分派
    :param on_progress: 進度回呼 (current, total, message)
    :param is_cancelled: 檢查是否取消的回呼
    :return: 處理結果列表
    """
    log().debug("「回覆」開始執行")

    option = get_option()
    undertakers = get_undertakers()
    articles = get_articles()
    cases = db.get_all_cases()
    results = []

    total = len(cases)
    for idx, row in enumerate(cases):
        if is_cancelled and is_cancelled():
            break

        reply_case = CaseReply.from_db_row(row)
        log().info(f"執行案件 {reply_case.number} ( {idx + 1} / {total} )")
        log().debug(reply_case.model_dump())

        # 跳過條件檢查
        skip_reason = _check_skip_conditions(reply_case, station_mode, articles)
        if skip_reason:
            log().error(f"【{reply_case.number}】{skip_reason}")
            results.append(
                {
                    "number": reply_case.number,
                    "action": "略過",
                    "success": False,
                    "reason": skip_reason,
                }
            )
            if on_progress:
                on_progress(
                    idx + 1, total, f"略過：{reply_case.number} - {skip_reason}"
                )
            continue

        reply_post = ReplyPostData(reply_case, option, articles)
        post_data = reply_post.post_data()

        # 非派出所模式且開啟重新分派
        if (
            not station_mode
            and re_assign
            and reply_case.undertaker != undertakers.get(10).name
        ):
            assign_case_by_post(reply_case.detail_url, undertakers.get(10), headers)

        # 送出回覆
        success = reply_by_post(reply_case.number, reply_case, headers, post_data)
        action = "回覆成功" if success else "回覆失敗"
        results.append(
            {"number": reply_case.number, "action": action, "success": success}
        )

        if on_progress:
            on_progress(idx + 1, total, f"{action}：{reply_case.number}")

    log().info("「回覆」執行完畢")
    return results


def _check_skip_conditions(
    reply_case: CaseReply, station_mode: bool, articles: dict
) -> str | None:
    """
    檢查案件是否需要跳過
    :return: 跳過原因字串，若不需跳過回傳 None
    """
    if reply_case.status == "已結案":
        return "已結案，不予執行"
    if reply_case.input == 0:
        return "未處理，不予執行"
    if reply_case.input == 100 and station_mode:
        return "不舉發，派出所模式不予執行"
    if reply_case.input == 100 and not reply_case.reject_answer:
        return "未填「不舉發理由」，請修正"
    if reply_case.input not in articles.keys():
        return "條款簡碼填寫錯誤，請修正"
    if (reply_case.input != 0 and reply_case.input != 100) and not reply_case.fine:
        return "未填「舉發單號」，請修正"
    return None


# ─────────────────── CLI 包裝（保留原有互動） ───────────────────


def reply(station_mode: bool = True, re_assign: bool = False) -> None:
    """
    執行回覆的主程式（CLI 版本）
    :param station_mode: 是否為派出所模式
    :param re_assign: 是否重新分派
    """
    log().debug("「回覆」開始執行")

    option = get_option()
    undertakers = get_undertakers()
    articles = get_articles()

    cases = db.get_all_cases()
    headers = get_intranet_headers()

    total = len(cases)
    for idx, row in enumerate(cases):
        reply_case = CaseReply.from_db_row(row)

        log().info(f"執行案件 {reply_case.number} ( {idx + 1} / {total} )")
        log().debug(reply_case.model_dump())

        skip_reason = _check_skip_conditions(reply_case, station_mode, articles)
        if skip_reason:
            log().error(f"【{reply_case.number}】{skip_reason}")
            continue

        reply_post = ReplyPostData(reply_case, option, articles)
        post_data = reply_post.post_data()

        if (
            not station_mode
            and re_assign
            and reply_case.undertaker != undertakers.get(10).name
        ):
            assign_case_by_post(reply_case.detail_url, undertakers.get(10), headers)

        if option.check:
            print(
                "\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500案件再次確認\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"
            )
            pprint.pprint(reply_case.model_dump())
            print("\n")
            print(post_data.Memo)
            check = input("\n\u25b3 是否確定回覆？（Y/n）")
            if check.upper() != "Y":
                log().error(f"【{reply_case.number}】取消回覆")
                continue

        reply_by_post(reply_case.number, reply_case, headers, post_data)

    log().info("「回覆」執行完畢")


# ─────────────────── 共用工具函式 ───────────────────


def reply_by_post(
    number: str, reply_case: CaseReply, headers: dict, post_data: ReplyPostPayload
) -> bool:
    """
    使用 post 方法回覆，成功後更新資料庫狀態
    :param number: 案號
    :param reply_case: 案件的物件
    :param headers: POST 標頭
    :param post_data: POST 資料（ReplyPostPayload）
    :return: 是否回覆成功
    """
    requests.post(
        url=reply_case.reply_url, headers=headers, data=post_data.model_dump()
    )

    check_case = get_case_detail(detail_url=reply_case.detail_url, headers=headers)

    if check_case.status == "已結案":
        db.update_case_status(number, check_case.status, check_case.undertaker)
        log().info(f"【{check_case.number}】回覆成功")
        return True
    else:
        log().error(f"【{check_case.number}】回覆失敗")
        return False
