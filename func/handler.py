import time
import requests
from utils.log import log
from utils.options import select_undertaker, Undertaker
from utils.excel import load_excel, save_excel
from utils.webdriver import open_browser, get_intranet_headers
from func.get import get, get_case_detail
from static.case import Case


def handle_case(url: str, undertaker: Undertaker, headers):
  """
  使用Post分派案件
  :param url: 案件原網址
  :param undertaker: 承辦人的物件
  :param headers: POST標頭
  :return: html狀態碼
  """
  post_data = {
    'HandlerId': undertaker.code,
    'AuditDays': 6,
  }
  handler_url = url.replace('Detail', 'Handler')

  res = requests.post(url=handler_url, headers=headers, data=post_data)  # 發送請求

  return res.status_code


def handle_lot():
  undertaker = select_undertaker()  # 選擇承辦人
  get(undertaker=undertaker)  # 抓取兼分派


def handle_one():
  """
  分派單一案件
  :return:
  """

  wb = load_excel('database')  # 開啟Excel
  ws = wb['ToDo']

  headers = get_intranet_headers()  # 取得標題

  browser = open_browser()  # 開啟瀏覽器
  browser.implicitly_wait(0.5)

  while True:
    time.sleep(0.5)
    x = input('\n△ 請輸入分派對象(退出請輸入0)：')
    if x == '0':
      break
    else:
      undertaker = select_undertaker()  # 選擇承辦人
      url = browser.current_url  # 取得當前網址
      handle_url = url if 'Handler' in url else url.replace('Detail', 'Handler')  # 取得分派網址
      detail_url = url.replace('Handler', 'Detail')  # 取得詳情網址

      status_code = handle_case(handle_url, undertaker, headers)  # 分派
      if status_code == 200:
        log().info(f'分派案件成功')
      else:
        log().warning(f'分派案件失敗，請重試，錯誤碼：{status_code}')
        continue

      case: Case = get_case_detail(detail_url, headers)  # 取得案件內容

      add_values = case.values() + [
        None,
        '=IF(U2=1,"已分派",IF(U2=2,"結案","處理中"))',
        0,
        '=VLOOKUP($P2,舉發法條!$A$2:$D$54,3,FALSE)',
        None,
        None,
        '=VLOOKUP($P2,舉發法條!$A$2:$D$54,2,FALSE)',
        1,
        0
      ]  # 要新增row的內容，要加上預設的內容

      ws.append(add_values)  # 新增案件
      save_excel(wb, 'database')  # 儲存Excel
