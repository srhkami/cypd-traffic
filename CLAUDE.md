# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 專案說明

本專案是針對嘉義縣警察局交通違規申訴案件的自動化處理工具，功能涵蓋：從內網案件管理系統擷取案件、分派承辦人、回覆案件（舉發/不舉發）、下載相關附件，以及維護 SQLite 案件資料庫。

所有程式碼的變數命名、註解、提交訊息、使用者介面文字，以及與本專案的所有對話，均須使用**台灣用語的繁體中文**。

## 執行方式

```bash
# 安裝相依套件（使用 uv）
uv sync

# 執行主程式
uv run python main.py

# 直接執行（若已啟動虛擬環境）
python main.py
```

打包為獨立執行檔：
```bash
uv run pyinstaller main.spec
```

**首次執行**：若 `data/` 目錄中存在舊版 `database.xlsx`，程式啟動時會自動偵測並提示是否將舊資料遷移至 SQLite。

執行時需在 `data/` 目錄下準備：
- `traffic.db`：SQLite 資料庫（首次啟動自動建立）
- `setting.xlsx`（僅初次遷移需要）：含「承辦人設定」與「選項」工作表
- `database.xlsx`（僅初次遷移需要）：含「Article」（法條）與「Todo」（案件）工作表

## 架構概覽

### 應用程式流程

```
main.py
 ├─ init_db()           ← 必須在所有模組 import 前執行
 └─ src/ui/menu.py      ← 所有使用者互動介面（主選單、子選單）
     ├─ src/features/get.py       ← 擷取案件（從內網爬取並寫入 SQLite）
     ├─ src/features/reply.py     ← 回覆案件（POST 送出回覆並更新 SQLite）
     ├─ src/features/download.py  ← 下載附件（HTTP 下載並存檔）
     └─ src/utils/excel_io.py     ← 匯出/匯入 Excel（資料管理選單）
```

### 資料層（SQLite）

資料庫位於 `data/traffic.db`，由 `src/utils/db.py` 統一管理，包含 4 張資料表：

| 資料表 | 說明 |
|--------|------|
| `cases` | 案件資料（主要動態資料） |
| `articles` | 法條對照表（簡碼 → 法條代碼 + 文字） |
| `undertakers` | 承辦人清單（派出所代號 → 人員資訊） |
| `options` | 系統選項（key-value 格式，6 個固定 key） |

**重要約束**：`db.py` 只能 import 標準庫、openpyxl 與 log，不可 import 任何 `src/models/` 下的 Pydantic 模型（避免循環依賴）。所有 DB 函式回傳 `sqlite3.Row`，由各 `models/*.py` 自行組裝 Pydantic 物件。

### 資料流

1. **驗證**：`webdriver.py` 開啟 Chrome 取得內網 Cookie，轉換為 `requests` 標頭
2. **爬取**：`get.py` 透過 BeautifulSoup 解析案件清單 HTML，呼叫 `db.insert_case()` 寫入 SQLite
3. **回填**：使用者透過「資料管理 → 匯出」取得 Excel，填入簡碼/單號/理由後「匯入」回 SQLite
4. **回覆**：`reply.py` 從 SQLite 讀取 `CaseReply`，建構 POST 資料後送出，成功後呼叫 `db.update_case_status()`
5. **設定**：承辦人、法條、選項均從 SQLite 讀取（首次由 Excel 遷移而來）

### 核心模組

| 模組 | 說明 |
|------|------|
| `src/utils/db.py` | SQLite 資料層：init_db、migrate_from_excel、所有 CRUD 函式 |
| `src/utils/excel_io.py` | 匯出案件 Excel（依狀態篩選）、從 Excel 匯入回填資料 |
| `src/features/get.py` | 從 `http://10.124.30.21/Mailbox?cid=5&page={n}` 分頁擷取案件，支援分派模式 |
| `src/features/reply.py` | 從 SQLite 讀取案件並批次送出 POST 回覆；含 `ReplyPostPayload`、`ReplyPostData` 與安全確認機制 |
| `src/features/download.py` | 依序下載所有案件附件，含重試次數限制與進度顯示 |
| `src/models/case.py` | `CaseWeb`（網頁擷取，含 `to_db_dict()`）與 `CaseReply`（含 `from_db_row()`）|
| `src/models/undertaker.py` | `Undertaker` 模型、`get_undertakers()`、`select_undertaker()`（互動式選擇） |
| `src/ui/menu.py` | 所有選單函式；`src/ui/info.py` 存放版本與更新日誌 |
| `src/utils/webdriver.py` | 控制 Chrome 瀏覽器進行內網驗證，取得 Cookie 後轉換為 HTTP 標頭 |

### 作業模式

- **派出所模式**（`station_mode=True`）：承辦人即為回覆人，直接結案
- **分局模式**（`station_mode=False`）：可選擇轉交分局承辦人或不重新分派

### 日期格式

程式內部使用中華民國曆（西元年 - 1911），由 `CaseWeb` 的 `@computed_field` 自動計算。SQLite 中以 `year_roc`、`month`、`day`、`hour`、`minute` 分欄儲存。

### Excel 匯出/匯入作業流程

1. 主選單 `（8）資料管理 → （1）匯出案件 Excel`
2. 選擇篩選條件（全部／未結案／已結案／未下載），產生 `data/export_{時間戳}.xlsx`
3. 在 Excel 的 P 欄（輸入簡碼）、R 欄（舉發單號）、S 欄（不舉發理由）填入資料
4. 主選單 `（8）資料管理 → （2）從 Excel 匯入回填資料`，選擇剛才的檔案即完成匯入

## 相依套件

- `selenium`：Chrome 瀏覽器自動化（內網驗證）
- `requests` + `beautifulsoup4`：HTTP 請求與 HTML 解析
- `openpyxl`：Excel 讀寫（匯出/匯入與首次遷移）
- `pydantic`：資料模型與型別驗證（`src/models/` 下所有資料類別）
- `pyinstaller`：打包為 Windows 獨立執行檔（dev 依賴）
