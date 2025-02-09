from static.info import ver
from utils.log import log
from func.get import get
from utils.excel import readonly_excel
from func.download import download

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
        '\n● 本程式於公務電腦中所有檔案操作，僅限於data資料下必要之檔案，並無修改、刪除、複製、新增、下載或上傳其他資料夾及檔案之功能。'
        '\n\n△ 注意事項：'
        '\n● 瀏覽器視窗開啟後勿隨意操作，請返回此程式操作，將兩個視窗並排顯示'
        '\n● 若瀏覽器開啟失敗，請將Chrome瀏覽器更新到最新版本')


def menu_main():
  print('\n┌──────────────────┐'
        '\n│（1）各所舉發作業 │'
        '\n├──────────────────┤'
        '\n│（2）分局交辦作業 │'
        '\n├──────────────────┤'
        '\n│（9）查看更新日誌 │'
        '\n├──────────────────┤'
        '\n│（0）退出程式     │'
        '\n└──────────────────┘')
  mode = input('請選擇模式：')
  log().debug(f'已選擇主功能{mode}')
  return mode


def menu_station():
  print('\n┌──────────────────┐'
        '\n│（1）抓取案件資料 │'
        '\n├──────────────────┤'
        '\n│（2）回覆案件     │'
        '\n├──────────────────┤'
        '\n│（3）下載檢舉檔案 │'
        '\n├──────────────────┤'
        '\n│（0）返回上一頁   │'
        '\n└──────────────────┘')
  mode = input('請選擇功能：')
  log().debug(f'已輸入次功能{mode}')

  while True:
    match mode:
      case '0':
        break
      case '1':
        menu_get()
      case '2':
        pass
        # df = readonly_excel('database')
        # wb = load_excel('reply')
        # ws = wb['Sheet']  # 讀取Excel
        # reply.reply(browser, df, ws, mode)  # 開始回覆
        # time_text = time.strftime('%d%H%M', time.localtime())  # 取得當前時間
        # save_excel(wb, f'reply_{time_text}')  # 另存一個Excel
      case '3':
        menu_download()  # 進入下載選單
      case _:
        log().warning('輸入錯誤，請重新輸入！')



  return mode


def menu_precinct():
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
  return mode


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



def tip_reply():
  print('\n◎ 本程式功能：從Excel檔讀取案件處理結果，逐一自動回覆'
        '\n△ 注意事項：'
        '\n● 請將「reply」檔案編輯完成後，放入「data」資料夾內'
        '\n● 警告！回覆時請勿點擊「回覆」按鍵，應在程式內操作！'
        )


def menu_get():
  print('\n◎ 本程式功能：透過網頁爬蟲，抓取每個檢舉案件的資訊，並儲存成Excel檔'
        '\n△ 注意事項：'
        '\n1. 執行前請確認「database」檔案已關閉，以免無法儲存資料。'
        '\n2. 本功能可以指定。'
        '\n3. 可指定起始日，亦可留空'
        '\n4. 執行到已抓取之案件時會自動停止抓取。')
  input('輸入任意鍵繼續……')
  get()