from bs4 import BeautifulSoup
from utils.webdriver import get_intranet_headers
from static.case import Case
import requests
from utils.excel import load_excel, save_excel
from utils.log import log


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


def get_case_detail(url, headers) -> Case:
  """
  取得案件詳情
  :param url: 案件網址
  :param headers: 標頭
  :return: 案件的物件
  """
  res = requests.post(url, headers=headers)  # 發送請求
  soup = BeautifulSoup(res.text, 'html.parser')  # 解析案件詳情頁面

  fieldset = soup.find('fieldset')  # 取得案件詳情表格
  tables = fieldset.find_all('table', attrs={'class': 'table-h'})  # 取得案件詳情表格
  tds = tables[0].find_all('td')  # 取得上方的表格內容
  tds2 = tables[1].find_all('td')  # 取得下方的表格內容

  case = Case(
    case_number=tds[0].text.strip(),
    url=url,
    place=tds[1].text.strip(),
    content=tds[2].text.strip(),
    sender=tds[3].text.strip(),
    undertaker=tds[12].text.strip(),
    time_all=tds2[0].text.strip(),
    car=tds2[1].text.strip(),
    files=[a['href'] for a in tds2[4].find_all('a')]
  )  # 將案件內容轉化為物件
  log().info(f'【{case.number}】取得詳情成功')

  return case


def get():
  headers = get_intranet_headers()  # 取得標頭

  wb = load_excel('database')  # 開啟Excel
  ws = wb['ToDo']

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
      case: Case = get_case_detail(f'http://10.124.30.21{url}', headers)
      ws.append(case.values())

    page += 1

  save_excel(wb, 'database')

  log().info('抓取案件執行結束。')

  input('輸入任意鍵繼續……')


if __name__ == '__main__':
  get()
