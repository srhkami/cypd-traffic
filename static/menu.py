from static.info import ver
from utils.log import log
from func.get import get
from func.reply import reply
from utils.excel import readonly_excel
from func.download import download
import time
from static.info import changelog

"""
給使用者查看的介面、選項
"""


def intro():
  print(f'◇ 嘉義縣民眾檢舉交通違規 自動化程式 v{ver}')
  print('作者：C.K.SAI 蔡智楷'
        '\n\n△ 開源及免責聲明'
        '\n● 本程式使用Python開發，原始碼均可供任何人查閱、複製及修改使用。'
        '\n● 本程式僅供嘉義縣警察局處理民眾檢舉交通違規承辦人員使用，使用範圍僅限公務用途。'
        '\n● 本程式於內網中各項操作僅為模擬瀏覽器點擊、複製及貼上文字，用以節省承辦人手動操作時間，無上傳、下載任何惡意軟體。'
        '\n● 本程式於公務電腦中所有檔案操作，僅限於本程式資料下必要之檔案，並無修改、刪除、複製、新增、下載或上傳其他資料夾及檔案之功能。'
        '\n\n△ 注意事項：'
        '\n● 任何需要輸入的地點請按『Enter』繼續下一步'
        '\n● 瀏覽器視窗開啟後請依指示操作，勿自行點擊其他地方以免導致程式出錯')


def menu_main():

  while True:
    time.sleep(0.3)
    print('\n┌──────────────────┐'
          '\n│（1）派出所 作業  │'
          '\n├──────────────────┤'
          '\n│（2）分局 作業    │'
          '\n├──────────────────┤'
          '\n│（9）查看更新日誌 │'
          '\n├──────────────────┤'
          '\n│（0）退出程式     │'
          '\n└──────────────────┘')
    mode = input('請輸入模式：')
    log().debug(f'已選擇主功能{mode}')

    match mode:
      case '1':
        menu_station()
      # case '2':
      #   menu_police_station(browser)
      case '9':
        print('\n△ 更新日誌：\n')
        for i in changelog:
          print(i)
        input('輸入任意鍵繼續……')
      # case '123':
      #   # 貼上網址會有雙引號，故先移除
      #   url = str(input('請輸入指定網址：')).replace('"', '')
      #   # url = url_test
      #   log().info('已啟用測試網址')
      case '0':
        log().debug('程式已結束')
        exit()
      case _:
        print('輸入錯誤，請重新輸入！')


def menu_station():

  while True:
    time.sleep(0.3)
    print('\n┌──────────────────┐'
          '\n│（1）抓取案件資料 │'
          '\n├──────────────────┤'
          '\n│（2）回覆案件     │'
          '\n├──────────────────┤'
          '\n│（3）下載檢舉影像 │'
          '\n├──────────────────┤'
          '\n│（0）返回上一頁   │'
          '\n└──────────────────┘')
    mode = input('請選擇功能：')
    log().debug(f'已輸入次功能{mode}')

    match mode:
      case '0':
        break
      case '1':
        menu_get()
        get()
      case '2':
        menu_reply()
        reply(mode)
      case '3':
        menu_download()  # 進入下載選單
      case _:
        log().warning('輸入錯誤，請重新輸入！')


def menu_precinct():
  while True:
    time.sleep(0.3)
    print('\n┌─────────────────────────┐'
          '\n│（1）分派案件 (批量模式) │'
          '\n├─────────────────────────┤'
          '\n│（2）分派案件 (個別模式) │'
          '\n├─────────────────────────┤'
          '\n│（3）抓取案件資料        │'
          '\n├─────────────────────────┤'
          '\n│（4）回覆案件            │'
          '\n├─────────────────────────┤'
          '\n│（0）返回上一頁          │'
          '\n└─────────────────────────┘')
    mode = input('請選擇功能：')
    log().debug(f'已選擇次功能{mode}')

    match mode:
      case '0':
        break
      case '1':
        pass
      case '2':
        pass
      case '3':
        menu_get()
        get()
      case '4':
        menu_reply()
        reply(mode)
      case _:
        log().warning('輸入錯誤，請重新輸入！')


def menu_download():
  print('\n◎ 本程式功能：從Excel檔取得檢舉檔案網址，自動下載檔案及生成網址QRcode'
        '\n△ 注意事項：'
        '\n● 請將包含網址的「output」檔案放入「data」資料夾中'
        '\n● 下載及輸出得檔案會依案件存放於「data」資料夾中'
        '\n● 下載檔案耗時較久，請耐心等候，建議不要一次下載過多案件'
        )
  check = input('是否確定開始下載？(Y/n)')

  if check.upper() == 'Y':
    download()


def menu_reply():
  print('\n◎ 本程式功能：從Excel檔讀取案件處理結果，逐一自動回覆'
        '\n△ 注意事項：'
        '\n● 請將「reply」檔案編輯完成後，放入「data」資料夾內'
        '\n● 警告！回覆時請勿點擊「回覆」按鍵，應在程式內操作！'
        )


def menu_get():
  print('\n◎ 本程式功能：透過網頁爬蟲，抓取每個檢舉案件的資訊，並儲存成Excel檔'
        '\n△ 注意事項：'
        '\n1. 執行前請確認「database」檔案已關閉，以免無法儲存資料。'
        '\n2. 本功能可以指定搜尋條件。'
        '\n3. 執行到「ToDo」資料表中已抓取過之案件時會自動跳過。')
  input('輸入任意鍵繼續……')
