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
    is_cancelled: Callable[[], bool] | None = None,
) -> list[dict]:
    """
    批次下載所有案件附件的核心邏輯
    :param on_progress: 進度回呼 (current, total, message)
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
        car = row["car"]
        file_links = json.loads(row["files_json"])
        dl_status = row["download_status"]

        log().info(f"執行第 {idx + 1} / {total} 案")

        if dl_status == 1:
            log().info(f"案件「{case_number}」已下載，略過")
            results.append({"number": case_number, "action": "略過", "success": True})
            if on_progress:
                on_progress(idx + 1, total, f"已下載，略過：{case_number}")
            continue

        download_single_case(case_number, car, file_links, option.download_limit)
        db.update_case_download_status(case_number)
        results.append({"number": case_number, "action": "下載完成", "success": True})

        if on_progress:
            on_progress(idx + 1, total, f"下載完成：{case_number}")

    log().info("「下載」執行完畢")
    return results


# ─────────────────── CLI 包裝（保留原有互動） ───────────────────


def download() -> None:
    """批次下載所有案件附件（CLI 版本）"""
    log().debug("「下載」開始執行")

    option = get_option()
    cases = db.get_all_cases()
    total = len(cases)

    for idx, row in enumerate(cases):
        case_number = row["number"]
        car = row["car"]
        file_links = json.loads(row["files_json"])
        dl_status = row["download_status"]

        log().info(f"執行第 {idx + 1} / {total} 案")

        if dl_status == 1:
            print(f"案件「{case_number}」案已下載，略過")
            continue

        download_single_case(case_number, car, file_links, option.download_limit)
        db.update_case_download_status(case_number)

    log().info("「下載」執行完畢")
    import time

    time.sleep(0.5)
    input("輸入任意鍵繼續……")


# ─────────────────── 共用工具函式 ───────────────────


def download_single_case(
    case_number: str, car: str, links: list[str], download_limit: int
) -> None:
    """
    下載單一案件的檔案
    :param case_number: 案號
    :param car: 車號
    :param links: 附件連結清單
    :param download_limit: 重試上限次數
    """
    log().info(f"開始下載「{case_number}」之檔案……")
    folder = rf".\download\{case_number}_{car}"
    try:
        os.mkdir(folder)
    except FileExistsError:
        pass
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
    with closing(requests.get(url, timeout=10, verify=False, stream=True)) as response:
        chunk_size = 1024
        content_size = int(response.headers["content-length"])
        data_count = 0
        print(f"{chunk_size},{content_size},{data_count}")
        with open(path, "wb") as file:
            for data in response.iter_content(chunk_size=chunk_size):
                file.write(data)
                done_block = int(data_count / content_size * 50)
                data_count = data_count + len(data)
                progress = data_count / content_size * 100
                print(
                    "\r %s [%s%s] %d%% "
                    % (
                        file_name + "：",
                        done_block * "\u2588",
                        " " * (50 - 1 - done_block),
                        progress,
                    ),
                    end=" ",
                )
    return progress
