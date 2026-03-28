import sqlite3
import json
import os
from src.utils.log import log

DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "traffic.db"
)

# 選項 key 與 Excel 列名的對應表
_OPTION_KEY_MAP = {
    "安全模式": "check",
    "顯示車號": "car",
    "顯示法條": "article",
    "舉發回覆": "text_y",
    "不舉發回覆": "text_n",
    "重下載次數": "download_limit",
}

_OPTION_DEFAULTS = {
    "check": "關閉",
    "car": "開啟",
    "article": "開啟",
    "text_y": "",
    "text_n": "",
    "download_limit": "3",
}

_conn: sqlite3.Connection | None = None


def get_conn() -> sqlite3.Connection:
    """取得模組層級的 SQLite 連線（單例，單執行緒 CLI 使用）"""
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
    return _conn


# ─────────────────── 初始化 ───────────────────


def init_db() -> None:
    """
    初始化資料庫：
    1. 建立 4 張資料表（若已存在則跳過）
    2. 插入 options 預設值（INSERT OR IGNORE）
    3. 若 cases 表為空且舊版 Excel 存在，提示一次性遷移
    """
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS cases (
            number       TEXT PRIMARY KEY,
            car          TEXT NOT NULL,
            detail_url   TEXT NOT NULL,
            place        TEXT NOT NULL,
            content      TEXT NOT NULL,
            sender       TEXT NOT NULL,
            year_roc     TEXT NOT NULL,
            month        TEXT NOT NULL,
            day          TEXT NOT NULL,
            hour         TEXT NOT NULL,
            minute       TEXT NOT NULL,
            files_json   TEXT NOT NULL,
            undertaker   TEXT NOT NULL,
            status       TEXT NOT NULL,
            input_code   INTEGER NOT NULL DEFAULT 0,
            fine         TEXT,
            reject_answer TEXT,
            download_status INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS articles (
            input_key  INTEGER PRIMARY KEY,
            code       INTEGER NOT NULL,
            text       TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS undertakers (
            station_id INTEGER PRIMARY KEY,
            unit       TEXT NOT NULL,
            name       TEXT NOT NULL,
            code       INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS options (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)

    for key, value in _OPTION_DEFAULTS.items():
        conn.execute(
            "INSERT OR IGNORE INTO options (key, value) VALUES (?, ?)", (key, value)
        )
    conn.commit()
    log().debug("資料庫初始化完成")

    # 偵測舊版 Excel，若 cases 表為空則記錄提示
    count = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
    db_xlsx = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "database.xlsx"
    )
    if count == 0 and os.path.exists(db_xlsx):
        log().info("偵測到舊版 Excel 資料，可透過設定頁面進行遷移")


def check_migration_available() -> dict:
    """
    檢查是否有舊版 Excel 可遷移
    :return: {
        'available': bool,       是否可執行遷移
        'has_database': bool,    是否有 database.xlsx
        'has_setting': bool,     是否有 setting.xlsx
        'cases_count': int       目前 cases 表的筆數
    }
    """
    data_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "data"
    )
    has_database = os.path.exists(os.path.join(data_dir, "database.xlsx"))
    has_setting = os.path.exists(os.path.join(data_dir, "setting.xlsx"))
    cases_count = get_conn().execute("SELECT COUNT(*) FROM cases").fetchone()[0]
    return {
        "available": has_database or has_setting,
        "has_database": has_database,
        "has_setting": has_setting,
        "cases_count": cases_count,
    }


def migrate_from_excel() -> dict:
    """
    一次性從舊版 Excel 遷移所有資料至 SQLite
    執行順序：articles → undertakers → options → cases
    :return: 各類資料遷移筆數
    """
    import openpyxl

    _data_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "data"
    )
    db_path = os.path.join(_data_dir, "database.xlsx")
    setting_path = os.path.join(_data_dir, "setting.xlsx")
    conn = get_conn()
    result = {"articles": 0, "cases": 0, "undertakers": 0, "options": False}

    # ── 法條 ──
    if os.path.exists(db_path):
        wb = openpyxl.load_workbook(db_path, data_only=True, read_only=True)
        if "Article" in wb.sheetnames:
            ws = wb["Article"]
            count = 0
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row[0] is None:
                    break
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO articles (input_key, code, text) VALUES (?, ?, ?)",
                        (int(row[0]), int(row[1]), str(row[2])),
                    )
                    count += 1
                except (ValueError, TypeError):
                    continue
            result["articles"] = count
            log().info(f"遷移法條：{count} 筆")

        # ── 案件 ──
        if "Todo" in wb.sheetnames:
            ws = wb["Todo"]
            count = 0
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row[0] is None:
                    break
                conn.execute(
                    """
                    INSERT OR IGNORE INTO cases
                    (number, car, detail_url, place, content, sender,
                     year_roc, month, day, hour, minute, files_json,
                     undertaker, status, input_code, fine, reject_answer, download_status)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                    (
                        row[0],  # number (A/1)
                        row[1],  # car (B/2)
                        row[2],  # detail_url (C/3)
                        row[3],  # place (D/4)
                        row[4],  # content (E/5)
                        row[5],  # sender (F/6)
                        row[6],  # year_roc (G/7)
                        row[7],  # month (H/8)
                        row[8],  # day (I/9)
                        row[9],  # hour (J/10)
                        row[10],  # minute (K/11)
                        row[11],  # files_json (L/12)
                        row[12],  # undertaker (M/13)
                        row[13],  # status (N/14)
                        # O/15 略過
                        row[15] if row[15] is not None else 0,  # input_code (P/16)
                        # Q/17 公式略過
                        row[17],  # fine (R/18)
                        row[18],  # reject_answer (S/19)
                        row[19] if row[19] is not None else 0,  # download_status (T/20)
                    ),
                )
                count += 1
            result["cases"] = count
            log().info(f"遷移案件：{count} 筆")
        wb.close()

    # ── 承辦人與選項 ──
    if os.path.exists(setting_path):
        wb = openpyxl.load_workbook(setting_path, data_only=True, read_only=True)

        if "承辦人設定" in wb.sheetnames:
            ws = wb["承辦人設定"]
            count = 0
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row[0] is None:
                    break
                conn.execute(
                    "INSERT OR IGNORE INTO undertakers (station_id, unit, name, code) VALUES (?,?,?,?)",
                    (int(row[0]), str(row[1]), str(row[2]), int(row[3])),
                )
                count += 1
            result["undertakers"] = count
            log().info(f"遷移承辦人：{count} 筆")

        if "選項" in wb.sheetnames:
            ws = wb["選項"]
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row[0] is None:
                    break
                key = _OPTION_KEY_MAP.get(str(row[0]))
                if key and row[1] is not None:
                    conn.execute(
                        "INSERT OR REPLACE INTO options (key, value) VALUES (?, ?)",
                        (key, str(row[1])),
                    )
            result["options"] = True
            log().info("遷移選項完成")
        wb.close()

    conn.commit()
    log().info("Excel 遷移全部完成")
    return result


# ─────────────────── 案件 CRUD ───────────────────


def get_case_numbers() -> list[str]:
    """回傳所有案件的案號清單（用於判斷是否重複）"""
    rows = get_conn().execute("SELECT number FROM cases").fetchall()
    return [row["number"] for row in rows]


def get_all_cases() -> list[sqlite3.Row]:
    """回傳所有案件（依插入順序）"""
    return get_conn().execute("SELECT * FROM cases ORDER BY rowid").fetchall()


def get_cases_by_status(status_filter: str | None) -> list[sqlite3.Row]:
    """
    依狀態篩選案件
    status_filter：None / '全部' / '未結案' / '已結案' / '未下載'
    """
    conn = get_conn()
    if status_filter is None or status_filter == "全部":
        return conn.execute("SELECT * FROM cases ORDER BY rowid").fetchall()
    elif status_filter == "未結案":
        return conn.execute(
            "SELECT * FROM cases WHERE status != '已結案' ORDER BY rowid"
        ).fetchall()
    elif status_filter == "已結案":
        return conn.execute(
            "SELECT * FROM cases WHERE status = '已結案' ORDER BY rowid"
        ).fetchall()
    elif status_filter == "未下載":
        return conn.execute(
            "SELECT * FROM cases WHERE download_status = 0 ORDER BY rowid"
        ).fetchall()
    return get_conn().execute("SELECT * FROM cases ORDER BY rowid").fetchall()


def insert_case(case_data: dict) -> None:
    """
    新增案件（若案號已存在則略過）
    case_data 須包含欄位：number, car, detail_url, place, content, sender,
                          year_roc, month, day, hour, minute, files_json,
                          undertaker, status
    """
    conn = get_conn()
    conn.execute(
        """
        INSERT OR IGNORE INTO cases
        (number, car, detail_url, place, content, sender,
         year_roc, month, day, hour, minute, files_json,
         undertaker, status)
        VALUES
        (:number, :car, :detail_url, :place, :content, :sender,
         :year_roc, :month, :day, :hour, :minute, :files_json,
         :undertaker, :status)
    """,
        case_data,
    )
    conn.commit()


def update_case_status(number: str, status: str, undertaker: str) -> None:
    """回覆成功後更新案件狀態與承辦人"""
    conn = get_conn()
    conn.execute(
        "UPDATE cases SET status=?, undertaker=? WHERE number=?",
        (status, undertaker, number),
    )
    conn.commit()


def update_case_download_status(number: str) -> None:
    """下載完成後標記 download_status = 1"""
    conn = get_conn()
    conn.execute("UPDATE cases SET download_status=1 WHERE number=?", (number,))
    conn.commit()


def batch_update_reply_fields(
    number: str, input_code: int, fine: str | None, reject_answer: str | None
) -> int:
    """
    從 Excel 匯入時，依案號更新回填欄位
    回傳實際更新的筆數（0 表示找不到該案號）
    """
    conn = get_conn()
    cursor = conn.execute(
        "UPDATE cases SET input_code=?, fine=?, reject_answer=? WHERE number=?",
        (input_code, fine, reject_answer, number),
    )
    conn.commit()
    return cursor.rowcount


# ─────────────────── 法條 ───────────────────


def get_articles_raw() -> list[sqlite3.Row]:
    """回傳所有法條資料"""
    return get_conn().execute("SELECT * FROM articles").fetchall()


def upsert_article(input_key: int, code: int, text: str) -> None:
    """
    新增或更新法條（以 input_key 為主鍵）
    :param input_key: 簡碼
    :param code: 代碼
    :param text: 法條內容
    """
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO articles (input_key, code, text) VALUES (?, ?, ?)",
        (input_key, code, text),
    )
    conn.commit()


def delete_article(input_key: int) -> int:
    """
    刪除指定簡碼的法條
    :param input_key: 簡碼
    :return: 刪除筆數（0 表示找不到）
    """
    conn = get_conn()
    cursor = conn.execute("DELETE FROM articles WHERE input_key = ?", (input_key,))
    conn.commit()
    return cursor.rowcount


# ─────────────────── 承辦人 ───────────────────


def get_undertakers_raw() -> list[sqlite3.Row]:
    """回傳所有承辦人資料"""
    return get_conn().execute("SELECT * FROM undertakers").fetchall()


def upsert_undertaker(station_id: int, unit: str, name: str, code: int) -> None:
    """
    新增或更新承辦人（以 station_id 為主鍵）
    :param station_id: 各所代號
    :param unit: 單位名稱
    :param name: 承辦人姓名
    :param code: 代碼
    """
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO undertakers (station_id, unit, name, code) VALUES (?, ?, ?, ?)",
        (station_id, unit, name, code),
    )
    conn.commit()


def delete_undertaker(station_id: int) -> int:
    """
    刪除指定代號的承辦人
    :param station_id: 各所代號
    :return: 刪除筆數（0 表示找不到）
    """
    conn = get_conn()
    cursor = conn.execute("DELETE FROM undertakers WHERE station_id = ?", (station_id,))
    conn.commit()
    return cursor.rowcount


# ─────────────────── 選項 ───────────────────


def get_options_raw() -> list[sqlite3.Row]:
    """回傳所有選項的 key-value 列表"""
    return get_conn().execute("SELECT key, value FROM options").fetchall()


def get_case_by_number(number: str) -> sqlite3.Row | None:
    """依案號取得單一案件"""
    return (
        get_conn().execute("SELECT * FROM cases WHERE number = ?", (number,)).fetchone()
    )


def update_option(key: str, value: str) -> int:
    """
    更新單一選項
    :param key: 選項 key
    :param value: 選項值
    :return: 更新筆數（0 表示找不到該 key）
    """
    conn = get_conn()
    cursor = conn.execute("UPDATE options SET value = ? WHERE key = ?", (value, key))
    conn.commit()
    return cursor.rowcount
