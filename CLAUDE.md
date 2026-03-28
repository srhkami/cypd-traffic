# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 專案說明

本專案是針對嘉義縣警察局交通違規申訴案件的自動化處理工具，功能涵蓋：從內網案件管理系統擷取案件、分派承辦人、回覆案件（舉發/不舉發）、下載相關附件，以及維護 Excel 案件資料庫。

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

執行時需要在同目錄下準備以下 Excel 設定檔：
- `setting.xlsx`：含「承辦人設定」與「選項」工作表
- `database.xlsx`：含「Article」（法條）工作表，以及每位承辦人的案件資料工作表

## 架構概覽

### 應用程式流程

```
main.py
 └─ src/static/menu.py     ← 所有使用者互動介面（主選單、子選單）
     ├─ src/features/get.py     ← 擷取案件（從內網爬取並寫入 Excel）
     ├─ src/features/reply.py   ← 回覆案件（POST 送出回覆並更新 Excel）
     └─ src/features/download.py← 下載附件（HTTP 下載並存檔）
```

### 資料流

1. **驗證**：`webdriver.py` 開啟 Chrome 取得內網 Cookie，轉換為 `requests` 標頭
2. **爬取**：`get.py` 透過 BeautifulSoup 解析案件清單 HTML，擷取案件詳情
3. **儲存**：案件資料以 `CaseWeb` 物件格式寫入 `database.xlsx` 的承辦人工作表
4. **回覆**：`reply.py` 從 Excel 讀取 `CaseReply` 物件，建構 POST 資料後送出
5. **設定**：承辦人資料、法條、系統選項均從 Excel 設定檔讀取

### 核心模組

| 模組 | 說明 |
|------|------|
| `src/features/get.py` | 從 `http://10.124.30.21/Mailbox?cid=5&page={n}` 分頁擷取案件，支援分派模式 |
| `src/features/reply.py` | 讀取 Excel 並批次送出 POST 回覆；含安全確認機制 |
| `src/features/download.py` | 依序下載所有案件附件，含重試次數限制與進度顯示 |
| `src/object/case.py` | `CaseWeb`（網頁擷取）與 `CaseReply`（Excel 回覆）兩種案件資料模型 |
| `src/object/post_data.py` | 建構回覆用 POST 資料，含備註格式化與舉發/不舉發判斷邏輯 |
| `src/object/undertaker.py` | 從 `setting.xlsx` 讀取承辦人清單，提供互動式選擇功能 |
| `src/utils/webdriver.py` | 控制 Chrome 瀏覽器進行內網驗證，取得 Cookie 後轉換為 HTTP 標頭 |
| `src/utils/excel.py` | 封裝 openpyxl 與 pandas 的 Excel 讀寫操作 |

### 作業模式

- **派出所模式**（`station_mode=True`）：承辦人即為回覆人，直接結案
- **分局模式**（`station_mode=False`）：可選擇轉交分局承辦人或不重新分派

### 日期格式

程式內部使用中華民國曆（西元年 - 1911），由 `CaseWeb` 於解析時自動轉換。

## 相依套件

- `selenium`：Chrome 瀏覽器自動化（內網驗證）
- `requests` + `beautifulsoup4`：HTTP 請求與 HTML 解析
- `openpyxl`：Excel 讀寫（含公式）
- `pandas`：以 DataFrame 格式讀取 Excel
- `pydantic`：資料模型與型別驗證（`src/object/` 下所有資料類別）
- `pyinstaller`：打包為 Windows 獨立執行檔（dev 依賴）
