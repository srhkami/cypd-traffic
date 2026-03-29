# AGENTS.md

本檔案提供給代理程式（Claude Code、Cursor Agent 等）在本專案工作時的指引。

## 專案概述

本專案是嘉義縣警察局交通違規申訴案件的自動化處理工具，使用 Python 開發，支援從內網系統擷取案件、分派承辦人、回覆案件、下載附件，以及維護 SQLite 資料庫。

本專案提供兩種執行模式：
- **CLI 模式**（`main.py`）：原有的命令列互動介面，使用 Selenium 進行內網認證
- **GUI 模式**（`main_gui.py`）：基於 pywebview + FastAPI 的桌面應用程式，提供 RESTful API 與網頁介面

**重要**：所有程式碼的變數命名、註解、提交訊息、使用者介面文字，均須使用**台灣用語的繁體中文**。

---

## 建置與執行指令

### 安裝相依套件
```bash
uv sync
```

### 執行 CLI 模式
```bash
uv run python main.py
```

### 執行 GUI 模式（pywebview + FastAPI）
```bash
uv run python main_gui.py
```

### 執行（已啟動虛擬環境）
```bash
python main.py       # CLI 模式
python main_gui.py   # GUI 模式
```

### 打包為獨立執行檔
```bash
uv run pyinstaller main.spec
```

### 測試
目前專案無測試檔案。若需新增測試，建議使用 `pytest`：
```bash
uv add --dev pytest
uv run pytest                    # 執行所有測試
uv run pytest tests/test_db.py   # 執行單一測試檔案
uv run pytest -v                 # 詳細輸出
```

---

## 程式碼風格指南

### 縮排與格式
- **使用 2 空格縮排**（非 4 空格）
- 頂層模組之間空 2 行，類別/函式之間空 1 行

### 命名慣例
| 類型 | 慣例 | 範例 |
|------|------|------|
| 類別 | PascalCase | `CaseWeb`, `Undertaker`, `ReplyPostPayload` |
| 函式/變數 | snake_case | `get_case_numbers()`, `update_case_status()` |
| 常數 | snake_case（全大寫） | `DB_PATH`, `OPTION_DEFAULTS` |
| Pydantic 欄位 | snake_case | `detail_url`, `input_code`, `reject_answer` |

### 類別結構範例
```python
class CaseWeb(BaseModel):
  """
  從網站上取得的案件內容，轉化為物件
  用以轉化為資料庫
  """
  number: str
  car: str
  url: str

  @computed_field
  @property
  def yy(self) -> str:
    return str(int(self.time_all[0:4]) - 1911)

  def to_db_dict(self) -> dict:
    """轉換為 db.insert_case() 所需的字典格式"""
    return {
      'number': self.number,
      'car': self.car,
      # ...
    }
```

### 類別方法順序
1. 文件字串（docstring）
2. 型別註釋（型別提示）
3. `@computed_field` 裝飾器的方法
4. `@field_validator` 裝飾器的方法
5. `@classmethod` 工廠方法
6. 執行方法

---

## 型別註釋

### 嚴格要求
- 所有函式參數與回傳值**必須**具備型別註釋
- 使用 `str | None` 而非 `Optional[str]`
- 使用 `list[str]` 而非 `List[str]`

```python
def get_case_numbers() -> list[str]:
    """回傳所有案件的案號清單"""

def insert_case(case_data: dict) -> None:
    """新增案件"""

def batch_update_reply_fields(
    number: str,
    input_code: int,
    fine: str | None,
    reject_answer: str | None
) -> int:
```

### Pydantic 模型
- 優先使用 Pydantic `BaseModel` 而非 `dataclass`
- 可選欄位使用 `= None` 提供預設值
- 使用 `@field_validator` 進行資料驗證
- 使用 `@computed_field` 產生計算屬性

```python
class CaseReply(BaseModel):
  number: str
  fine: str | None = None
  reject_answer: str | None = None

  @field_validator('undertaker', mode='before')
  @classmethod
  def take_last_three(cls, v):
    if isinstance(v, str):
      return v[-3:]
    return v
```

---

## 錯誤處理與日誌

### 日誌使用
使用 `src/utils/log.py` 中的 `log()` 函式，**勿使用 `print()`** 輸出資訊：

```python
from src.utils.log import log

log().debug('詳細除錯資訊')   # 除錯用
log().info('一般操作資訊')    # 操作成功
log().warning('警示但可繼續') # 警告
log().error('錯誤訊息')       # 錯誤（不中斷）
```

### 錯誤處理原則
- 例外時記錄錯誤：`log().error('錯誤描述', exc_info=True)`
- 失敗時回傳 `None` 或拋出例外由上層處理
- 不在 `db.py` 中 import 任何 `src/models/` 下的模組（避免循環依賴）

---

## SQLite 資料庫規範

### 資料表設計
- 所有 DB 函式回傳 `sqlite3.Row`（非字典）
- 由各 `models/*.py` 自行組裝 Pydantic 物件

```python
def get_all_cases() -> list[sqlite3.Row]:
    """回傳所有案件（依插入順序）"""
    return get_conn().execute('SELECT * FROM cases ORDER BY rowid').fetchall()
```

### Pydantic 組裝方式
```python
@classmethod
def from_db_row(cls, row: sqlite3.Row) -> 'CaseReply':
    """從 SQLite Row 物件建立"""
    return cls(
        number=row['number'],
        car=row['car'],
        # ...
    )
```

---

## 匯入模組順序

依以下順序排列 `import` 陳述式：

1. 標準庫
2. 第三方套件（`requests`, `openpyxl`, `pydantic` 等）
3. 本地相對匯入（`from src.utils...`, `from src.models...`）

```python
import sqlite3
import json
import os

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, computed_field

from src.utils.log import log
from src.models.case import CaseWeb
```

---

## 函式/方法文件字串

所有公開函式**必須**包含文件字串，說明：
- 功能用途
- 參數含義
- 回傳值

```python
def migrate_from_excel() -> None:
    """
    一次性從舊版 Excel 遷移所有資料至 SQLite
    執行順序：articles → undertakers → options → cases
    """
```

---

## 特殊約定

### 中華民國曆
程式內部使用 ROC 曆（西元年 - 1911），由 `CaseWeb` 的 `@computed_field` 自動計算：
```python
@computed_field
@property
def yy(self) -> str:
    return str(int(self.time_all[0:4]) - 1911)
```

### 日期欄位設計
SQLite 中以 `year_roc`、`month`、`day`、`hour`、`minute` 分欄儲存。

### 分頁與迴圈
- 使用 `while True` + `break` 進行分頁爬取
- 使用 `enumerate()` 取得索引以顯示進度

---

## GUI 模式架構（pywebview + FastAPI）

### 執行流程
`main_gui.py` 啟動時的執行順序：
1. 初始化資料庫（`init_db()`）
2. 在背景執行緒啟動 FastAPI（uvicorn，預設隨機可用連接埠）
3. 在主執行緒啟動 pywebview 視窗，**直接載入本地前端頁面**
4. 使用者可直接操作資料庫（案件列表、設定、Excel 匯出匯入等）
5. 需要內網操作時，手動點擊「登入內網」按鈕觸發認證
6. 認證流程：前端呼叫 `pywebview.api.login()` → 開新視窗連到內網 → 取得 Cookie → 自動關閉認證視窗

### API 回應格式
所有 API 端點回傳統一格式：
```json
{"success": true, "message": "操作說明", "data": ...}
```
使用 `src/api/deps.py` 中的 `ok()` 與 `fail()` 函式產生回應。

### 背景任務機制
長時間操作（擷取案件、回覆案件、下載附件）使用背景任務模式：
1. 前端發送 `POST` 請求啟動任務
2. 後端建立 `TaskInfo` 物件，回傳 `task_id`
3. 前端輪詢 `GET /api/tasks/{task_id}` 取得進度
4. 任務狀態：`pending` → `running` → `completed` / `failed` / `cancelled`

### features 模組解耦
每個 features 模組拆分為「核心邏輯」與「CLI 包裝」：
- **核心函式**（如 `scrape_cases()`）：接收 cookie 參數，回傳結果，不涉及 UI 互動
- **CLI 包裝**（如 `get_case_cli()`）：呼叫核心函式，處理 CLI 輸入/輸出
- API 路由呼叫核心函式，CLI 選單呼叫 CLI 包裝

### 認證機制
- **CLI 模式**：使用 `src/utils/webdriver.py`（Selenium）開啟 Chrome 取得 cookie
- **GUI 模式**：使用 `src/utils/auth.py`（CookieStore 單例）管理 pywebview 取得的 cookie

---

## 目錄結構

```
src/
 ├─ __init__.py
 ├─ api/                # FastAPI RESTful API（GUI 模式）
 │   ├─ __init__.py
 │   ├─ app.py          # FastAPI 應用程式工廠（create_app）
 │   ├─ deps.py         # 共用依賴（ok/fail 回應函式）
 │   ├─ schemas.py      # API 請求/回應 Pydantic 模型
 │   ├─ tasks.py        # 背景任務管理（TaskInfo, TaskStatus）
 │   └─ routes/         # 路由模組
 │       ├─ articles.py     # 法條 CRUD
 │       ├─ auth.py         # 認證狀態查詢
 │       ├─ cases.py        # 案件 CRUD
 │       ├─ download.py     # 附件下載（背景任務）
 │       ├─ excel.py        # Excel 匯出/匯入
 │       ├─ options.py      # 設定選項 CRUD
 │       ├─ reply.py        # 回覆案件（背景任務）
 │       ├─ scrape.py       # 擷取案件（背景任務）
 │       ├─ tasks.py        # 任務狀態查詢
 │       └─ undertakers.py  # 承辦人 CRUD
 ├─ features/           # 主要功能模組
 │   ├─ get.py          # 擷取案件（scrape_cases 核心 + CLI 包裝）
 │   ├─ reply.py        # 回覆案件（reply_cases 核心 + CLI 包裝）
 │   └─ download.py     # 下載附件（download_all_cases 核心 + CLI 包裝）
 ├─ models/             # Pydantic 資料模型
 │   ├─ case.py
 │   ├─ undertaker.py
 │   ├─ article.py
 │   └─ options.py
 ├─ ui/                 # CLI 使用者介面
 │   ├─ menu.py
 │   └─ info.py
 ├─ utils/              # 工具函式
 │   ├─ auth.py         # Cookie 管理（CookieStore 單例）
 │   ├─ db.py           # SQLite 資料層
 │   ├─ excel_io.py     # Excel 讀寫（含核心函式 + CLI 包裝）
 │   ├─ log.py          # 日誌設定
 │   └─ webdriver.py    # Selenium Chrome 控制（CLI 模式）
 └─ web/                # GUI 前端靜態檔案
     ├─ index.html      # 主頁面
     ├─ style.css       # 樣式
     └─ app.js          # 前端邏輯
```

---

## 已完成功能與已知問題

### 已完成功能（GUI 模式）

以下功能已在 GUI 模式中實作完成：

1. **SQLite 跨執行緒修正**：`db.py` 中 `sqlite3.connect()` 加入 `check_same_thread=False`，因本專案為單一使用者桌面應用，低並行風險
2. **承辦人 CRUD**（行內編輯）：
   - 後端：`db.py` 新增 `upsert_undertaker()`、`delete_undertaker()`
   - API：`POST /api/undertakers`（upsert）、`DELETE /api/undertakers/{station_id}`
   - 前端：行內 `<input>` 編輯、儲存/刪除按鈕、新增列
3. **法條 CRUD**（行內編輯）：
   - 後端：`db.py` 新增 `upsert_article()`、`delete_article()`
   - API：`POST /api/articles`（upsert）、`DELETE /api/articles/{input_key}`
   - 前端：同承辦人的行內編輯模式
4. **資料遷移功能**：
   - `db.py` 新增 `check_migration_available()`，移除 `init_db()` 中的 `input()` 阻塞呼叫
   - `migrate_from_excel()` 改為回傳 `dict` 結果，修正 Article 表中間標題列的 `ValueError`
   - API：`GET /api/excel/migrate/status`、`POST /api/excel/migrate`
   - 前端：設定頁面的遷移區塊，含狀態檢查、確認對話框、遷移後自動重載
5. **前端設定頁面重構**：`loadSettings()` 拆分為獨立的 `loadOptions()`、`loadUndertakers()`、`loadArticles()`、`loadMigration()`，各自有 `try/catch`
6. **承辦人/法條主鍵規則**：`station_id`（承辦人）、`input_key`（法條）為使用者輸入值，使用 `INSERT OR REPLACE` 處理新增與更新，既有列的主鍵欄位設為 `readonly`
7. **下載功能重構**：
   - 資料夾路徑從 `files/{案號}_{車號}` 簡化為 `files/{案號}`
   - 移除 `download_status` 資料庫欄位，改以 `files/{案號}/` 資料夾是否存在判斷下載狀態
   - 新增 `download_case_by_number()` 核心函式，支援單一案件強制重新下載
   - API：`POST /api/tasks/download/{case_number}` 單一案件下載端點
   - `files.py` 路由移除 `car` 參數，路徑簡化為 `/api/files/{case_number}`
8. **案件詳情彈窗強化**：
   - 新增「案件網址」欄位，以 `target="_blank"` 超連結顯示 `detail_url`
   - 新增「回填資訊」可編輯區塊（簡碼、舉發單號、不舉發理由），串接 `PATCH /api/cases/{number}/reply-fields`
   - 移除列表頁行內編輯（inline-input），改為在彈窗中統一操作
   - 移除列表頁「操作」欄位
9. **法條快取與簡碼即時校驗**：
   - 前端建立 `_articleCache`（`{ input_key: text }`），從 `GET /api/articles` 取得並快取
   - 簡碼輸入時即時比對法條表，存在時顯示綠色法條文字，不存在時顯示紅色警告並禁用儲存按鈕
   - 簡碼為 0 視為「未設定」，始終允許儲存
   - 設定頁面異動法條時呼叫 `invalidateArticleCache()` 清除快取
10. **重新下載按鈕**：彈窗附件區塊新增「重新下載」按鈕，觸發單一案件下載背景任務，下載中禁用按鈕並顯示進度，完成後自動重新載入檔案列表
11. **API 回應型別修正**：`files.py`（3 個端點）與 `app.py`（`get_version`）的回傳型別從 `dict` 修正為 `ApiResponse`，解決 FastAPI `ResponseValidationError`
12. **CLI 修正**：
    - `reply.py`：將 `post_data()` 建構移至 `_check_skip_conditions()` 之後，避免應略過的案件觸發錯誤
    - `menu.py`：統一縮排為 4 空格
    - `excel_io.py`：移除 `download_status` 相關欄位與「未下載」篩選選項
13. **移除無用程式碼**：刪除 `GET /api/excel/files` 端點、`list_importable_files` import、`CaseOut.download_status` 欄位、前端「未下載」篩選選項

### 已知問題與待改善項目

目前無已知問題。

---

## 禁止事項

- **嚴禁** commit secrets、API keys 或任何敏感資訊
- **禁止**在 `db.py` 中 import `src/models/` 下的模組
- **禁止**使用 `print()` 取代 `log()`（除 CLI 選單顯示外）
- **禁止**建立測試檔案（如 `test_*.py`）於根目錄，請使用 `tests/` 目錄
