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
        _conn = sqlite3.connect(DB_PATH)
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

    # 偵測舊版 Excel，若 cases 表為空則提示遷移
    count = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
    db_xlsx = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "database.xlsx"
    )
    if count == 0 and os.path.exists(db_xlsx):
        answer = input("\n△ 偵測到舊版 Excel 資料，是否立即遷移至資料庫？(Y/n) ")
        if answer.strip().upper() == "Y":
            migrate_from_excel()


def migrate_from_excel() -> None:
    """
    一次性從舊版 Excel 遷移所有資料至 SQLite
    執行順序：articles → undertakers → options → cases
    """
    import openpyxl

    _data_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "data"
    )
    db_path = os.path.join(_data_dir, "database.xlsx")
    setting_path = os.path.join(_data_dir, "setting.xlsx")
    conn = get_conn()

    # ── 法條 ──
    if os.path.exists(db_path):
        wb = openpyxl.load_workbook(db_path, data_only=True, read_only=True)
        if "Article" in wb.sheetnames:
            ws = wb["Article"]
            count = 0
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row[0] is None:
                    break
                conn.execute(
                    "INSERT OR IGNORE INTO articles (input_key, code, text) VALUES (?, ?, ?)",
                    (int(row[0]), int(row[1]), str(row[2])),
                )
                count += 1
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
            log().info("遷移選項完成")
        wb.close()

    conn.commit()
    log().info("Excel 遷移全部完成")


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


# ─────────────────── 承辦人 ───────────────────


def get_undertakers_raw() -> list[sqlite3.Row]:
    """回傳所有承辦人資料"""
    return get_conn().execute("SELECT * FROM undertakers").fetchall()


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
