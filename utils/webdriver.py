from selenium import webdriver
from selenium.webdriver.common.by import By
# from undetected_chromedriver import Chrome
from utils.log import log
from static.html import tags
from static.case import CaseReply
from utils.options import Option


# Chrome瀏覽器設定
# options = webdriver.EdgeOptions()
# options.add_experimental_option("excludeSwitches", ["enable-automation"])
# options.add_experimental_option('useAutomationExtension', False)
# options.add_experimental_option("prefs", {
#   "profile.password_manager_enabled": False, "credentials_enable_service": False})


def open_browser():
  # try:
  browser = webdriver.Edge()  # 開啟瀏覽器
  browser.get('http://10.124.30.21')  # 開啟首頁
  log().debug('瀏覽器開啟成功')
  # except:
  #   log().critical('瀏覽器開啟失敗，請檢查瀏覽器版本是否最新！', exc_info=True)
  #   input('輸入任意鍵離開……')
  browser.implicitly_wait(10)  # 預設尋找標籤等待時間
  return browser


# 函數：取得Xpath元素
def fx(browser, xpath):
  return browser.find_element(By.XPATH, xpath)


def into_mailbox(browser):
  # 點擊「信箱模組」
  browser.find_element(By.XPATH, tags['信箱模組']).click()
  # 點擊「交通違規信箱」
  browser.find_element(By.XPATH, tags['交通違規信箱']).click()


def get_intranet_headers(mode: str = 'N') -> dict:
  """
  使用瀏覽器取得向內網發送請求的標題
  :param mode: 「N」沒有動作, 「F」取得表單內容
  :return: 內網標頭
  """
  browser = open_browser()  # 打開瀏覽器
  browser.get('http://10.124.30.21')  # 開啟首頁

  if mode == 'F':
    # Form表單模式
    # 內網信箱送出表單後，會取得一個session儲存於cookie中，取得此cookie才能順利取得搜尋結果清單
    into_mailbox(browser)  # 進入檢舉信箱
    print('現在可以指定搜尋條件，請按下搜尋後再返回程式。')
    input('輸入任意鍵繼續……')

  cookies = browser.get_cookies()  # 取得cookie，是一個清單

  if not cookies:
    log().error('cookie取得失敗')

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

  log().info('成功建立標頭')

  return headers


class ReplyPostData:
  def __init__(self, case: CaseReply, option: Option):
    self.case = case
    self.option = option

  def post_data(self) -> dict:

    reply_text = '您於本縣警察局交通違規檢舉專區檢舉違規案件，經處理後茲答覆如下：\n'  # 回覆文字

    if self.case.select == 100:
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
        reply_text += f'舉發法條： {self.case.article} 。\n'

      reply_text += self.option.text_y  # 加入罐頭訊息

      return {
        'Memo': reply_text,
        'Status': '第一次回覆',
        'IsEnd': '是',
        'isReport': '否' if self.case.select == 100 else '是',
        'MailboxTrafficCatalogRejectId': 1,
        'MailboxTrafficArchiveTitle': self.case.fine,
        'MailboxTrafficCatalogBackgroundId': self.case.select,
      }
