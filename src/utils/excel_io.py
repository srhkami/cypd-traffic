import os
from datetime import datetime

import openpyxl

from src.utils import db
from src.utils.log import log

# Todo 工作表欄位標題（對應原 database.xlsx 格式）
_TODO_HEADERS = [
    "案號",
    "車號",
    "案件詳情網址",
    "違規地點",
    "違規內容",
    "檢舉人",
    "違規年份",
    "月份",
    "日期",
    "時",
    "分",
    "附件清單",
    "承辦人",
    "狀態",
    "（保留）",
    "輸入簡碼",
    "法條（自動）",
    "舉發單號",
    "不舉發理由",
]

_STATUS_OPTIONS = {
    "1": None,
    "2": "未結案",
    "3": "已結案",
}


# ─────────────────── 核心邏輯（無 input() 互動） ───────────────────


def export_cases_core(status_filter: str | None = None) -> dict:
    """
    匯出案件至 Excel 的核心邏輯
    :param status_filter: 篩選條件：None / '全部' / '未結案' / '已結案' / '未下載'
    :return: {'filepath': str, 'count': int} 或 {'error': str}
    """
    cases = db.get_cases_by_status(status_filter)
    articles = db.get_articles_raw()

    if not cases:
        return {"error": "符合條件的案件為 0 筆，取消匯出"}

    wb = openpyxl.Workbook()

    # ── Todo 工作表 ──
    ws_todo = wb.active
    ws_todo.title = "Todo"
    ws_todo.append(_TODO_HEADERS)

    for row_num, case in enumerate(cases, start=2):
        row_data = [
            case["number"],
            case["car"],
            case["detail_url"],
            case["place"],
            case["content"],
            case["sender"],
            case["year_roc"],
            case["month"],
            case["day"],
            case["hour"],
            case["minute"],
            case["files_json"],
            case["undertaker"],
            case["status"],
            None,
            case["input_code"],
            f"=VLOOKUP($P{row_num},Article!$A$2:$D$54,3,FALSE)",
            case["fine"],
            case["reject_answer"],
        ]
        ws_todo.append(row_data)

    # ── Article 工作表 ──
    ws_article = wb.create_sheet("Article")
    ws_article.append(["簡碼", "法條代碼", "法條文字"])
    for art in articles:
        ws_article.append([art["input_key"], art["code"], art["text"]])

    # ── 儲存 ──
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    data_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "data"
    )
    filename = f"export_{timestamp}.xlsx"
    filepath = os.path.join(data_dir, filename)
    wb.save(filepath)

    log().info(f"匯出案件 {len(cases)} 筆，檔案：{filepath}")
    return {"filepath": filepath, "filename": filename, "count": len(cases)}


def import_reply_fields_core(filepath: str) -> dict:
    """
    從 Excel 匯入回填資料的核心邏輯
    :param filepath: Excel 檔案完整路徑
    :return: {'updated': int, 'skipped': int} 或 {'error': str}
    """
    wb = openpyxl.load_workbook(filepath, data_only=True)

    if "Todo" not in wb.sheetnames:
        return {"error": "找不到 Todo 工作表，取消匯入"}

    ws = wb["Todo"]
    updated = 0
    skipped = 0

    for row_num in range(2, ws.max_row + 1):
        number = ws.cell(row_num, 1).value
        if not number:
            continue

        input_code = ws.cell(row_num, 16).value
        if not input_code:
            skipped += 1
            continue

        fine = ws.cell(row_num, 18).value
        reject_answer = ws.cell(row_num, 19).value

        count = db.batch_update_reply_fields(
            str(number),
            int(input_code),
            str(fine) if fine is not None else None,
            str(reject_answer) if reject_answer is not None else None,
        )
        updated += count

    log().info(
        f"從 {os.path.basename(filepath)} 匯入：更新 {updated} 筆，略過 {skipped} 筆"
    )
    return {"updated": updated, "skipped": skipped}


def list_importable_files() -> list[str]:
    """
    列出 data/ 目錄下可匯入的 xlsx 檔案名稱
    :return: 檔案名稱列表
    """
    data_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "data"
    )
    return sorted(
        [
            f
            for f in os.listdir(data_dir)
            if f.endswith(".xlsx") and f not in ("database.xlsx", "setting.xlsx")
        ]
    )


def get_data_dir() -> str:
    """取得 data/ 目錄的絕對路徑"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")


# ─────────────────── CLI 包裝（保留原有互動） ───────────────────


def export_cases_to_excel() -> None:
    """互動式匯出案件至 Excel（CLI 版本）"""
    print(
        "\n◎ 本程式功能：將案件資料匯出為 Excel 檔"
        "\n\u25b3 篩選條件："
        "\n（1）全部"
        "\n（2）未結案"
        "\n（3）已結案"
    )
    mode = input("請選擇篩選條件：").strip()
    status_filter = _STATUS_OPTIONS.get(mode)
    if mode not in _STATUS_OPTIONS:
        log().warning("輸入無效，預設匯出全部案件")
        status_filter = None

    result = export_cases_core(status_filter)

    if "error" in result:
        print(f"\u25b3 {result['error']}")
    else:
        print(f"\n\u2713 已匯出 {result['count']} 筆案件至：{result['filepath']}")

    input("輸入任意鍵繼續……")


def import_reply_fields_from_excel() -> None:
    """互動式從 Excel 匯入回填資料（CLI 版本）"""
    xlsx_files = list_importable_files()

    if not xlsx_files:
        print("\u25b3 在 data 資料夾中找不到可匯入的 xlsx 檔案。")
        input("輸入任意鍵繼續……")
        return

    print("\n◎ 請選擇要匯入的檔案：")
    for i, f in enumerate(xlsx_files, start=1):
        print(f"（{i}）{f}")

    choice = input("請輸入編號：").strip()
    try:
        filename = xlsx_files[int(choice) - 1]
    except (ValueError, IndexError):
        log().warning("輸入無效，取消匯入")
        return

    filepath = os.path.join(get_data_dir(), filename)
    result = import_reply_fields_core(filepath)

    if "error" in result:
        print(f"\u25b3 {result['error']}")
    else:
        print(
            f"\n\u2713 匯入完成：更新 {result['updated']} 筆，略過 {result['skipped']} 筆（未填入簡碼）"
        )

    input("輸入任意鍵繼續……")
