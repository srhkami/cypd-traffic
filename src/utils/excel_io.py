import os
from datetime import datetime
import openpyxl
from src.utils import db
from src.utils.log import log

# Todo 工作表欄位標題（對應原 database.xlsx 格式）
_TODO_HEADERS = [
  '案號', '車號', '案件詳情網址', '違規地點', '違規內容', '檢舉人',
  '違規年份', '月份', '日期', '時', '分', '附件清單',
  '承辦人', '狀態', '（保留）', '輸入簡碼', '法條（自動）',
  '舉發單號', '不舉發理由', '下載狀態',
]

_STATUS_OPTIONS = {
  '1': None,
  '2': '未結案',
  '3': '已結案',
  '4': '未下載',
}


def export_cases_to_excel() -> None:
  """
  互動式匯出案件至 Excel（可依狀態篩選）
  匯出格式同原 Todo 工作表（20 欄），並附帶 Article 工作表供 VLOOKUP 參照
  """
  print('\n◎ 本程式功能：將案件資料匯出為 Excel 檔'
        '\n△ 篩選條件：'
        '\n（1）全部'
        '\n（2）未結案'
        '\n（3）已結案'
        '\n（4）未下載'
        )
  mode = input('請選擇篩選條件：').strip()
  status_filter = _STATUS_OPTIONS.get(mode)
  if mode not in _STATUS_OPTIONS:
    log().warning('輸入無效，預設匯出全部案件')
    status_filter = None

  cases = db.get_cases_by_status(status_filter)
  articles = db.get_articles_raw()

  if not cases:
    print('△ 符合條件的案件為 0 筆，取消匯出。')
    return

  wb = openpyxl.Workbook()

  # ── Todo 工作表 ──
  ws_todo = wb.active
  ws_todo.title = 'Todo'
  ws_todo.append(_TODO_HEADERS)

  for row_num, case in enumerate(cases, start=2):
    row_data = [
      case['number'],          # A (1)  案號
      case['car'],             # B (2)  車號
      case['detail_url'],      # C (3)  案件詳情網址
      case['place'],           # D (4)  違規地點
      case['content'],         # E (5)  違規內容
      case['sender'],          # F (6)  檢舉人
      case['year_roc'],        # G (7)  違規年份（民國）
      case['month'],           # H (8)  月份
      case['day'],             # I (9)  日期
      case['hour'],            # J (10) 時
      case['minute'],          # K (11) 分
      case['files_json'],      # L (12) 附件清單 JSON
      case['undertaker'],      # M (13) 承辦人
      case['status'],          # N (14) 狀態
      None,                    # O (15) 保留
      case['input_code'],      # P (16) 輸入簡碼
      f'=VLOOKUP($P{row_num},Article!$A$2:$D$54,3,FALSE)',  # Q (17) 法條公式
      case['fine'],            # R (18) 舉發單號
      case['reject_answer'],   # S (19) 不舉發理由
      case['download_status'], # T (20) 下載狀態
    ]
    ws_todo.append(row_data)

  # ── Article 工作表 ──
  ws_article = wb.create_sheet('Article')
  ws_article.append(['簡碼', '法條代碼', '法條文字'])
  for art in articles:
    ws_article.append([art['input_key'], art['code'], art['text']])

  # ── 儲存 ──
  timestamp = datetime.now().strftime('%Y%m%d_%H%M')
  filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', f'export_{timestamp}.xlsx')
  wb.save(filename)

  print(f'\n✓ 已匯出 {len(cases)} 筆案件至：{filename}')
  log().info(f'匯出案件 {len(cases)} 筆，檔案：{filename}')

  input('輸入任意鍵繼續……')


def import_reply_fields_from_excel() -> None:
  """
  互動式從 Excel 匯入回填資料（input_code、fine、reject_answer）
  依案號比對後更新資料庫，僅更新 input_code 不為 0 的列
  """
  data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')
  xlsx_files = sorted([
    f for f in os.listdir(data_dir)
    if f.endswith('.xlsx') and f not in ('database.xlsx', 'setting.xlsx')
  ])

  if not xlsx_files:
    print('△ 在 data 資料夾中找不到可匯入的 xlsx 檔案。')
    input('輸入任意鍵繼續……')
    return

  print('\n◎ 請選擇要匯入的檔案：')
  for i, f in enumerate(xlsx_files, start=1):
    print(f'（{i}）{f}')

  choice = input('請輸入編號：').strip()
  try:
    filename = xlsx_files[int(choice) - 1]
  except (ValueError, IndexError):
    log().warning('輸入無效，取消匯入')
    return

  filepath = os.path.join(data_dir, filename)
  wb = openpyxl.load_workbook(filepath, data_only=True)

  if 'Todo' not in wb.sheetnames:
    print('△ 找不到 Todo 工作表，取消匯入。')
    input('輸入任意鍵繼續……')
    return

  ws = wb['Todo']
  updated = 0
  skipped = 0

  for row_num in range(2, ws.max_row + 1):
    number = ws.cell(row_num, 1).value
    if not number:
      continue

    input_code = ws.cell(row_num, 16).value
    if not input_code:
      skipped += 1
      continue  # 未填入簡碼，略過

    fine = ws.cell(row_num, 18).value
    reject_answer = ws.cell(row_num, 19).value

    count = db.batch_update_reply_fields(
      str(number), int(input_code),
      str(fine) if fine is not None else None,
      str(reject_answer) if reject_answer is not None else None,
    )
    updated += count

  print(f'\n✓ 匯入完成：更新 {updated} 筆，略過 {skipped} 筆（未填入簡碼）')
  log().info(f'從 {filename} 匯入：更新 {updated} 筆，略過 {skipped} 筆')
  input('輸入任意鍵繼續……')
