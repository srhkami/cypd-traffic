import os
import json
from typing import Callable
from contextlib import closing

import requests

from src.utils.log import log
from src.models.options import get_option
from src.utils import db


# ─────────────────── 核心邏輯（無 input() 互動） ───────────────────


def download_all_cases(
    on_progress: Callable[[int, int, str], None] | None = None,
    on_result: Callable[[dict], None] | None = None,
    is_cancelled: Callable[[], bool] | None = None,
) -> list[dict]:
    """
    批次下載所有案件附件的核心邏輯
    以 files/{案號}/ 資料夾是否存在來判斷是否已下載
    :param on_progress: 進度回呼 (current, total, message)
    :param on_result: 每筆案件處理完成時的回呼 (result_dict)
    :param is_cancelled: 檢查是否取消的回呼
    :return: 處理結果列表
    """
    log().debug("「下載」開始執行")

    option = get_option()
    cases = db.get_all_cases()
    total = len(cases)
    results = []

    for idx, row in enumerate(cases):
        if is_cancelled and is_cancelled():
            break

        case_number = row["number"]
        file_links = json.loads(row["files_json"])
        folder = os.path.join("files", case_number)

        log().info(f"執行第 {idx + 1} / {total} 案")

        if os.path.isdir(folder):
            log().info(f"案件「{case_number}」已下載，略過")
            result = {"number": case_number, "action": "略過", "success": True}
            results.append(result)
            if on_result:
                on_result(result)
            if on_progress:
                on_progress(idx + 1, total, f"已下載，略過：{case_number}")
            continue

        download_single_case(case_number, file_links, option.download_limit)
        result = {"number": case_number, "action": "下載完成", "success": True}
        results.append(result)
        if on_result:
            on_result(result)

        if on_progress:
            on_progress(idx + 1, total, f"下載完成：{case_number}")

    log().info("「下載」執行完畢")
    return results


def download_case_by_number(case_number: str) -> dict:
    """
    下載單一案件的附件（強制重新下載，覆蓋既有檔案）
    :param case_number: 案號
    :return: 處理結果字典
    """
    row = db.get_case_by_number(case_number)
    if row is None:
        return {
            "number": case_number,
            "action": "失敗",
            "success": False,
            "reason": "找不到案號",
        }

    file_links = json.loads(row["files_json"])
    if not file_links:
        return {
            "number": case_number,
            "action": "略過",
            "success": True,
            "reason": "此案件沒有附件",
        }

    option = get_option()
    download_single_case(case_number, file_links, option.download_limit)
    return {"number": case_number, "action": "下載完成", "success": True}


# ─────────────────── CLI 包裝（保留原有互動） ───────────────────


def download() -> None:
    """批次下載所有案件附件（CLI 版本）"""
    log().debug("「下載」開始執行")

    option = get_option()
    cases = db.get_all_cases()
    total = len(cases)

    for idx, row in enumerate(cases):
        case_number = row["number"]
        file_links = json.loads(row["files_json"])
        folder = os.path.join("files", case_number)

        log().info(f"執行第 {idx + 1} / {total} 案")

        if os.path.isdir(folder):
            log().info(f"案件「{case_number}」已下載，略過")
            continue

        download_single_case(case_number, file_links, option.download_limit)

    log().info("「下載」執行完畢")
    import time

    time.sleep(0.5)
    input("輸入任意鍵繼續……")


# ─────────────────── 共用工具函式 ───────────────────


def download_single_case(
    case_number: str, links: list[str], download_limit: int
) -> None:
    """
    下載單一案件的檔案
    :param case_number: 案號
    :param links: 附件連結清單
    :param download_limit: 重試上限次數
    """
    log().info(f"開始下載「{case_number}」之檔案……")
    folder = os.path.join("files", case_number)
    os.makedirs(folder, exist_ok=True)
    for index, url in enumerate(links):
        file_name = url.split("/")[-1:][0]
        log().debug(f"{file_name} 開始下載")
        path = f"{folder}/{file_name}"
        download_times = 0
        while True:
            progress = download_file(url, path)
            if progress == 100:
                log().info(f"{file_name} 下載成功({index}/{len(links)})")
                break
            if download_limit == download_times:
                log().error(
                    f"{file_name} 下載嘗試次數已達上限，跳過本檔案，請手動下載。"
                )
                break
            else:
                download_times += 1
                log().error("下載內容不完整，重新開始下載。")
    log().info(f"「{case_number}」所有檔案下載完畢")


def download_file(url: str, path: str) -> float:
    """
    串流下載單一檔案，顯示進度條
    :param url: 檔案網址
    :param path: 儲存路徑
    :return: 下載進度百分比（100 表示完成）
    """
    file_name = os.path.basename(path)
    progress = 0.0
    with closing(requests.get(url, timeout=10, verify=False, stream=True)) as response:
        chunk_size = 1024
        content_size = int(response.headers["content-length"])
        data_count = 0
        log().debug(f"chunk_size={chunk_size}, content_size={content_size}")
        last_logged = 0
        with open(path, "wb") as file:
            for data in response.iter_content(chunk_size=chunk_size):
                file.write(data)
                data_count = data_count + len(data)
                progress = data_count / content_size * 100
                milestone = int(progress // 25) * 25
                if milestone > last_logged:
                    log().debug(f"{file_name}：下載進度 {milestone}%")
                    last_logged = milestone
    return progress
