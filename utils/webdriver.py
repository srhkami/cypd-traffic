from selenium import webdriver
from utils.log import log
from static.case import CaseReply
from utils.options import Option, Article, get_articles
from selenium.webdriver.common.by import By

articles = get_articles()  # 取得法條對應表

def into_mailbox(browser):
  # 點擊「信箱模組」
  browser.find_element(By.XPATH, '/html[1]/body[1]/div[2]/div[1]/ul[1]/li[1]/div[1]/a[1]').click()
  # 點擊「交通違規信箱」
  browser.find_element(By.XPATH, '/html[1]/body[1]/div[2]/div[1]/ul[1]/li[1]/div[1]/ul[1]/li[4]/a[1]').click()


def open_browser():
  browser = webdriver.Chrome()  # 開啟瀏覽器
  browser.get('http://10.124.30.21')  # 開啟首頁
  log().debug('瀏覽器開啟成功')
  browser.implicitly_wait(10)  # 預設尋找標籤等待時間
  into_mailbox(browser)  # 進入交通違規信箱
  return browser


def get_intranet_headers(mode: str = 'N') -> dict:
  """
  使用瀏覽器取得向內網發送請求的標題
  :param mode: 「N」沒有動作, 「F」取得表單內容
  :return: 內網標頭
  """
  browser = open_browser()  # 打開瀏覽器

  if mode == 'F':
    # Form表單模式
    # 內網信箱送出表單後，會取得一個session儲存於cookie中，取得此cookie才能順利取得搜尋結果清單
    # into_mailbox(browser)  # 進入檢舉信箱
    print('現在可以指定搜尋條件，請按下『搜尋按鈕』後再返回程式。')
    input('輸入任意鍵繼續……')

  cookies = browser.get_cookies()  # 取得cookie，是一個清單

  if not cookies:
    log().error('cookie取得失敗')
  log().debug(f'成功取得cookie:{cookies}')

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


class ReplyPostData:
  def __init__(self, case: CaseReply, option: Option):
    self.case = case
    self.option = option

  def post_data(self) -> dict:

    reply_text = '您於本縣警察局交通違規檢舉專區檢舉違規案件，經處理後茲答覆如下：\n'  # 回覆文字

    if self.case.input == 100:
      # 不舉發的情況
      log().debug('本案為不舉發')
      reply_text += self.case.reject_answer  # 加入不舉發回覆
      reply_text += self.option.text_n  # 加入罐頭訊息

    else:
      # 舉發的情況
      log().debug('本案為舉發')

      if self.option.car:  # 加入違規車號
        reply_text += f'違規車號： {self.case.car}。\n'

      if self.option.article:  # 加入舉發法條
        reply_text += f'舉發法條： {articles[self.case.input].text} 。\n'

      reply_text += self.option.text_y  # 加入罐頭訊息

      reply_post_data = {
        'Memo': reply_text,
        'Status': '第一次回覆',
        'IsEnd': '是',
        'isReport': '否' if self.case.input == 100 else '是',
        'MailboxTrafficCatalogRejectId': 1,
        'MailboxTrafficArchiveTitle': self.case.fine,
        'MailboxTrafficCatalogBackgroundId': articles[self.case.input].code,
      }

      log().debug(reply_post_data)

      return reply_post_data
