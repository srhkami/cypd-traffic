import time
from typing import Callable

import requests
from bs4 import BeautifulSoup

from src.utils.log import log
from src.utils.webdriver import get_intranet_headers, open_browser
from src.models.undertaker import select_undertaker, Undertaker, get_undertakers
from src.models.case import CaseWeb
from src.utils import db


# ─────────────────── 核心邏輯（無 input() 互動） ───────────────────


def scrape_cases(
    headers: dict,
    handle_mode: bool = False,
    undertaker: Undertaker | None = None,
    on_progress: Callable[[int, int, str], None] | None = None,
    is_cancelled: Callable[[], bool] | None = None,
) -> list[dict]:
    """
    爬取案件的核心邏輯（不含 CLI 互動）
    :param headers: 內網 HTTP 標頭
    :param handle_mode: 是否為分派模式
    :param undertaker: 分派模式下的承辦人
    :param on_progress: 進度回呼 (current, total, message)
    :param is_cancelled: 檢查是否取消的回呼
    :return: 處理結果列表 [{'number': ..., 'action': ..., 'success': ...}]
    """
    todo_case_list = db.get_case_numbers()
    results = []

    page = 1
    case_url_list = []

    # 分頁爬取清單
    while True:
        if is_cancelled and is_cancelled():
            break

        list_url = f"http://10.124.30.21/Mailbox?cid=5&page={page}"
        res = requests.get(list_url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        log().info(f"讀取清單頁面 {list_url}")

        case_urls = get_cases_in_page(soup)
        if not case_urls:
            log().info("沒有找到下一頁，執行結束")
            break

        case_url_list += case_urls
        page += 1

    total = len(case_url_list)
    if on_progress:
        on_progress(0, total, f"共找到 {total} 筆案件")

    # 逐案處理
    for idx, url in enumerate(case_url_list):
        if is_cancelled and is_cancelled():
            break

        full_url = f"http://10.124.30.21{url}"

        if handle_mode and undertaker:
            case = assign_case_by_post(full_url, undertaker, headers)
            if not case:
                results.append({"number": "未知", "action": "分派", "success": False})
                if on_progress:
                    on_progress(idx + 1, total, f"分派失敗：{url}")
                continue
        else:
            case = get_case_detail(full_url, headers)

        if case.number in todo_case_list:
            log().info(f"【{case.number}】已存在資料，不予儲存")
            results.append({"number": case.number, "action": "略過", "success": True})
        else:
            db.insert_case(case.to_db_dict())
            action = "分派並儲存" if handle_mode else "儲存"
            results.append({"number": case.number, "action": action, "success": True})

        if on_progress:
            on_progress(idx + 1, total, f"已處理 {case.number}")

    log().info("抓取案件執行結束。")
    return results


# ─────────────────── CLI 包裝（保留原有互動） ───────────────────


def get(handle_mode: bool = False) -> None:
    """
    抓取案件的主程式（CLI 版本）
    :param handle_mode: 分派模式，若為 True，則會選擇承辦人進行分派
    """
    headers = get_intranet_headers(mode="F")

    undertaker = None
    if handle_mode:
        undertaker = select_undertaker()

    scrape_cases(headers, handle_mode, undertaker)

    input("輸入任意鍵繼續……")


# ─────────────────── 共用工具函式 ───────────────────


def get_cases_in_page(soup) -> list:
    """
    在頁面中取得初步的案件清單
    :param soup: BeautifulSoup 物件
    :return: 案件詳情網址的列表
    """
    table = soup.find(name="table", attrs={"class": "table"})
    trs = table.find_all("tr")[1:]

    if not trs:
        return []

    case_urls = []
    for tr in trs:
        tds = tr.find_all("td")
        case_urls.append(tds[1].a["href"])

    return case_urls


def get_case_detail(detail_url: str, headers: dict) -> CaseWeb:
    """
    取得案件詳情
    :param detail_url: 案件網址
    :param headers: 標頭
    :return: 案件的物件
    """
    res = requests.get(detail_url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    fieldset = soup.find("fieldset")
    tables = fieldset.find_all("table", attrs={"class": "table-h"})
    tds = tables[0].find_all("td")
    tds2 = tables[1].find_all("td")

    case = CaseWeb(
        number=tds[0].text.strip(),
        url=detail_url,
        place=tds[1].text.strip(),
        content=tds[2].text.strip(),
        sender=tds[3].text.strip(),
        undertaker=tds[12].text.strip(),
        status=tds[16].text.strip(),
        time_all=tds2[0].text.strip(),
        car=tds2[1].text.strip(),
        files=[a["href"] for a in tds2[4].find_all("a")],
    )
    log().info(f"【{case.number}】取得詳情成功")
    log().debug(case.model_dump())

    return case


def assign_case_by_post(
    detail_url: str, undertaker: Undertaker, headers: dict
) -> CaseWeb | None:
    """
    使用 Post 分派案件
    :param detail_url: 案件詳情網址
    :param undertaker: 承辦人的物件
    :param headers: POST 標頭
    :return: 案件或空
    """
    post_data = {
        "HandlerId": undertaker.code,
        "AuditDays": 6,
    }
    handler_url = detail_url.replace("Details", "Handler")
    res = requests.post(url=handler_url, headers=headers, data=post_data)
    log().debug(res)
    case = get_case_detail(detail_url, headers)
    if case.undertaker[-3:] == undertaker.name:
        log().info(f"【{case.number}】分派成功")
        return case
    else:
        log().error(f"【{case.number}】分派失敗")
        return None


def assign_single_case() -> None:
    """分派單一案件（CLI 互動版本）"""
    todo_case_list = db.get_case_numbers()

    headers = get_intranet_headers()

    browser = open_browser()
    browser.implicitly_wait(0.5)

    while True:
        time.sleep(0.5)
        undertakers = get_undertakers()

        x = input("\n\u25b3 請輸入分派對象(退出請輸入0)：")
        if x == "0":
            log().info("停止執行分派")
            browser.quit()
            break

        undertaker: Undertaker = undertakers.get(int(x))
        if not undertaker:
            log().warning("承辦人輸入錯誤，請重試")
            continue

        log().info(f"已選擇 {undertaker.unit}-{undertaker.name}")
        url = browser.current_url
        log().debug(f"當前網址：{url}")
        if "Details" not in url and "Handler" not in url:
            log().warning("並未在案件網頁中，請進入案件再執行")
            continue

        detail_url = url if "Details" in url else url.replace("Handler", "Details")

        case = assign_case_by_post(detail_url, undertaker, headers)

        if not case:
            continue

        if case.number not in todo_case_list:
            db.insert_case(case.to_db_dict())

        browser.back()
        browser.refresh()
