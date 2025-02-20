from bs4 import BeautifulSoup
import time
import requests
from utils.log import log
from utils.options import Undertaker, get_undertakers, select_undertaker
from utils.excel import load_excel, save_excel
from utils.webdriver import open_browser, get_intranet_headers
from static.case import Case


def get_case_list_table(soup) -> list:
  """
  取得案件清單
  :param soup:
  :return: 案件詳情網址的列表
  """
  table = soup.find(name='table', attrs={'class': 'table'})  # 取得案件清單主表格
  trs = table.find_all('tr')[1:]  # 取得表格中tbody的所有tr

  if not trs:
    # 如果沒有資料了，回覆空清單
    return []

  case_urls = []  # 建立空清單：案件詳情網址的列表
  for tr in trs:
    tds = tr.find_all('td')
    case_urls.append(tds[1].a['href'])  # 將案件詳情的連結加入

  return case_urls


def get_case_detail(detail_url, headers) -> Case:
  """
  取得案件詳情
  :param detail_url: 案件網址
  :param headers: 標頭
  :return: 案件的物件
  """
  res = requests.get(detail_url, headers=headers)  # 發送請求
  soup = BeautifulSoup(res.text, 'html.parser')  # 解析案件詳情頁面

  fieldset = soup.find('fieldset')  # 取得案件詳情表格
  tables = fieldset.find_all('table', attrs={'class': 'table-h'})  # 取得案件詳情表格
  tds = tables[0].find_all('td')  # 取得上方的表格內容
  tds2 = tables[1].find_all('td')  # 取得下方的表格內容

  case = Case(
    case_number=tds[0].text.strip(),
    url=detail_url,
    place=tds[1].text.strip(),
    content=tds[2].text.strip(),
    sender=tds[3].text.strip(),
    undertaker=tds[12].text.strip(),
    status=tds[16].text.strip(),
    time_all=tds2[0].text.strip(),
    car=tds2[1].text.strip(),
    files=[a['href'] for a in tds2[4].find_all('a')]
  )  # 將案件內容轉化為物件
  log().info(f'【{case.number}】取得詳情成功')
  log().debug(case.to_dict())

  return case


def get(handle_mode: bool = False):
  """
  抓取案件的主程式
  :param handle_mode: 分派模式，若為True，則會選擇承辦人進行分派
  :return:
  """

  headers = get_intranet_headers(mode='F')  # 取得標頭，使用表單模式

  if handle_mode:
    # 如果開始分派模式
    undertaker = select_undertaker()  # 選擇承辦人

  wb = load_excel('database')  # 開啟Excel
  ws = wb['Todo']

  todo_case_list = [cell.value for cell in ws['A']]  # 已存在的清單

  page = 1  # 清單頁數
  while True:
    list_url = f'http://10.124.30.21/Mailbox?cid=5&page={page}'  # 清單的網址

    res = requests.get(list_url, headers=headers)  # 發送請求
    soup = BeautifulSoup(res.text, 'html.parser')  # 解析清單頁面
    log().info(f'讀取清單頁面 {list_url}')

    case_urls = get_case_list_table(soup)

    if not case_urls:
      log().info('沒有找到下一頁，執行結束')
      break

    for url in case_urls:

      if handle_mode:
        # 如果為分派模式，分派並抓取案件
        case: Case | None = handle_case(f'http://10.124.30.21{url}', undertaker, headers)
        if not case:
          # 分派失敗，不儲存該筆
          continue

      else:
        # 如果沒有傳入承辦人，正常抓取
        case: Case = get_case_detail(f'http://10.124.30.21{url}', headers)

      if case.number in todo_case_list:
        # 如果案件已存在
        log().info(f'【{case.number}】已存在資料，不予抓取')
        continue

      add_values = case.values() + [
        None,
        0,
        '=VLOOKUP($P2,舉發法條!$A$2:$D$54,3,FALSE)',
        None,
        None,
        0
      ]  # 要新增row的內容，要加上預設的內容

      ws.append(add_values)  # 新增案件

    page += 1

  save_excel(wb, 'database')

  log().info('抓取案件執行結束。')

  input('輸入任意鍵繼續……')


def handle_case(detail_url: str, undertaker: Undertaker, headers) -> Case | None:
  """
  使用Post分派案件
  :param detail_url: 案件詳情網址
  :param undertaker: 承辦人的物件
  :param headers: POST標頭
  :return: 案件或空
  """
  post_data = {
    'HandlerId': undertaker.code,
    'AuditDays': 6,
  }
  handler_url = detail_url.replace('Details', 'Handler')
  # log().debug(f'分派網址{handler_url}')
  res = requests.post(url=handler_url, headers=headers, data=post_data)  # 發送請求
  log().debug(res)
  case: Case = get_case_detail(detail_url, headers)  # 取得案件詳情
  if case.undertaker[-3:] == undertaker.name:
    # 如果承辦人已更改，返回案件
    return case
  else:
    # 如果承辦人未更改，返回 None
    log().error(f'【{case.number}】分派失敗')
    return None


def handle_one():
  """
  分派單一案件
  :return:
  """

  wb = load_excel('database')  # 開啟Excel
  ws = wb['Todo']

  headers = get_intranet_headers()  # 取得標題

  browser = open_browser()  # 開啟瀏覽器
  browser.implicitly_wait(0.5)

  while True:
    time.sleep(0.5)
    undertakers = get_undertakers()

    x = input('\n△ 請輸入分派對象(退出請輸入0)：')
    if x == '0':
      log().info('停止執行分派')
      browser.quit()
      break

    undertaker: Undertaker = undertakers.get(int(x))
    if not undertaker:
      log().warning('承辦人輸入錯誤，請重試')
      continue

    log().info(f'已選擇 {undertaker.unit}-{undertaker.name}')
    url = browser.current_url  # 取得當前網址
    if 'Details' not in url or 'Handler' not in url:
      log().warning('並未在案件網頁中，請進入案件再執行')
      continue

    detail_url = url if 'Details' in url else url.replace('Handler', 'Details')  # 取得詳情網址

    case: Case | None = handle_case(detail_url, undertaker, headers)  # 分派並抓取案件
    if not case:
      continue

    add_values = case.values() + [
      None,
      0,
      '=VLOOKUP($P2,舉發法條!$A$2:$D$54,3,FALSE)',
      None,
      None,
      0
    ]  # 要新增row的內容，要加上預設的內容

    ws.append(add_values)  # 新增案件
    save_excel(wb, 'database')  # 儲存Excel


if __name__ == '__main__':
  get()
