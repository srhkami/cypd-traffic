# from selenium import webdriver
# from selenium.webdriver.common.by import By
from src.utils.log import log
import json


# def into_mailbox(browser):
#   # 點擊「信箱模組」
#   browser.find_element(By.XPATH, '/html[1]/body[1]/div[2]/div[1]/ul[1]/li[1]/div[1]/a[1]').click()
#   # 點擊「交通違規信箱」
#   browser.find_element(By.XPATH, '/html[1]/body[1]/div[2]/div[1]/ul[1]/li[1]/div[1]/ul[1]/li[4]/a[1]').click()


# def open_browser():
#   browser = webdriver.Chrome()  # 開啟瀏覽器
#   browser.get('http://10.124.30.21')  # 開啟首頁
#   log().debug('瀏覽器開啟成功')
#   browser.implicitly_wait(10)  # 預設尋找標籤等待時間
#   into_mailbox(browser)  # 進入交通違規信箱
#   return browser


# def get_intranet_headers(mode: str = 'N') -> dict:
#   """
#   使用瀏覽器取得向內網發送請求的標題
#   :param mode: 「N」沒有動作, 「F」取得表單內容
#   :return: 內網標頭
#   """
#   browser = open_browser()  # 打開瀏覽器
#
#   if mode == 'F':
#     # Form表單模式
#     # 內網信箱送出表單後，會取得一個session儲存於cookie中，取得此cookie才能順利取得搜尋結果清單
#     # into_mailbox(browser)  # 進入檢舉信箱
#     print('現在可以指定搜尋條件，請按下『搜尋按鈕』後再返回程式。')
#     input('輸入任意鍵繼續……')
#
#   cookies = browser.get_cookies()  # 取得cookie，是一個清單
#
#   if not cookies:
#     log().error('cookie取得失敗')
#   log().debug(f'成功取得cookie:{cookies}')
#
#   # 將cookie轉換為字串，方便加入headers中
#   cookie_content = ''  # cookie的內容
#   for cookie in cookies:
#     cookie_content += f'{cookie["name"]}={cookie["value"]}; '
#   cookie_content = cookie_content[:-2]  # 移除最後兩個字
#
#   headers = {
#     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
#     'Accept-Encoding': 'gzip, deflate',
#     'Accept-Language': 'zh-TW,zh',
#     'Connection': 'keep-alive',
#     'Cookie': cookie_content,
#     'Host': '10.124.30.21',
#     'Referer': 'http://10.124.30.21/',
#     'Sec-GPC': '1',
#     'Upgrade-Insecure-Requests': '1',
#   }
#   log().info('成功取得標頭，程式將繼續執行……')
#   log().debug(headers)
#
#   return headers


def get_intranet_headers(mode: str = 'N') -> dict:
  """
  todo: 暫時性的解決方案
  自行取得cookie字串貼上，再開始執行
  :param mode: 「N」沒有動作, 「F」取得表單內容
  :return: 內網標頭
  """
  # browser = open_browser()  # 打開瀏覽器

  if mode == 'F':
    # Form表單模式
    # 內網信箱送出表單後，會取得一個session儲存於cookie中，取得此cookie才能順利取得搜尋結果清單
    # into_mailbox(browser)  # 進入檢舉信箱
    print('現在可以指定搜尋條件，請按下『搜尋按鈕』後再返回程式。')
    input('輸入任意鍵繼續……')

  # cookies = browser.get_cookies()  # 取得cookie，是一個清單

  try:
    with open('cookies.json', 'r', encoding='UTF-8') as json_file:
      cookies = json.load(json_file)
  except Exception as e:
    log().error(f'cookie取得失敗，{e}')

  # if not cookies:
  #   log().error('cookie取得失敗')
  log().info(f'成功取得cookie:{cookies}')

  # 將cookie轉換為字串，方便加入headers中
  cookie_content = ''  # cookie的內容
  for cookie in cookies:
    cookie_content += f'{cookie["name"]}={cookie["value"]}; '
  cookie_content = cookie_content[:-2]  # 移除最後兩個字

  headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-TW,zh',
    'Connection': 'keep-alive',
    'Cookie': cookie_content,
    'Host': '10.124.30.21',
    'Referer': 'http://10.124.30.21/',
    'Sec-GPC': '1',
    'Upgrade-Insecure-Requests': '1',
  }
  log().info('成功取得標頭，程式將繼續執行……')
  log().debug(headers)

  return headers
