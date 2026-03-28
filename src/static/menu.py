from src.static.info import ver
from src.utils.log import log
from src.features.get import get, assign_single_case
from src.features.reply import reply
from src.features.download import download
from src.utils.excel_io import export_cases_to_excel, import_reply_fields_from_excel
import time
from src.static.info import changelog
from pprint import pprint

"""
給使用者查看的介面、選項
"""


def intro():
  print(f'◇ 嘉義縣民眾檢舉交通違規 自動化程式 v{ver}')
  print('作者：C.K.SAI 蔡智楷'
        '\n\n△ 開源及免責聲明'
        '\n● 本程式使用Python開發，原始碼均可供任何人查閱、複製及修改使用。'
        '\n● 本程式僅供嘉義縣警察局處理民眾檢舉交通違規承辦人員使用，節省手動操作時間，使用範圍僅限公務用途。'
        '\n● 本程式於公務電腦中所有檔案操作，僅限於本程式資料下必要之檔案，並無修改、刪除、複製、新增、下載或上傳其他資料夾及檔案之功能。'
        '\n\n△ 注意事項：'
        '\n● 任何需要輸入的地點請按『Enter』繼續下一步。'
        '\n● 瀏覽器視窗開啟後請依指示操作。')


def menu_main():
  while True:
    time.sleep(0.3)
    print('\n --------------------'
          '\n ◎ 主選單'
          '\n（1）派出所作業'
          '\n（2）分局 作業'
          '\n（8）資料管理'
          '\n（9）查看更新日誌'
          '\n（0）退出程式'
          '\n --------------------'
          )
    mode = input('請輸入模式：')
    log().debug(f'已選擇主功能{mode}')

    match mode:
      case '1':
        menu_station()
      case '2':
        menu_precinct()
      case '8':
        menu_data()
      case '9':
        print('\n△ 更新日誌：\n')
        pprint(changelog)
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
        print('找不到選項，請重新輸入！')


def menu_station():
  """
  分局選單
  :return:
  """
  while True:
    time.sleep(0.3)
    print('\n --------------------'
          '\n  ◎ 派出所作業'
          '\n（1）抓取案件資料'
          '\n（2）回覆案件'
          '\n（9）下載檢舉影像'
          '\n（0）返回上一頁'
          '\n --------------------'
          )
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
        reply(True)
      case '9':
        menu_download()  # 進入下載選單
      case _:
        log().warning('找不到選項，請重新輸入！')


def menu_precinct():
  """
  派出所選單
  :return:
  """
  while True:
    time.sleep(0.3)
    print('\n --------------------'
          '\n  ◎ 分局作業 '
          '\n（1）分派案件 (批量模式) '
          '\n（2）分派案件 (個別模式) '
          '\n（3）抓取案件資料'
          '\n（4）回覆案件（分派回自己）'
          '\n（5）回覆案件（不重新分派）'
          '\n（9）下載檢舉影像'
          '\n（0）返回上一頁'
          '\n --------------------'
          )
    mode = input('請選擇功能：')
    log().debug(f'已選擇次功能{mode}')

    match mode:
      case '0':
        break
      case '1':
        menu_handle_lot()
        get(handle_mode=True)  # 抓取兼分派
      case '2':
        menu_handle_one()
        assign_single_case()
      case '3':
        menu_get()
        get()
      case '4':
        menu_reply()
        reply(station_mode=False, re_assign=True)
      case '5':
        menu_reply()
        reply(station_mode=False, re_assign=False)
      case '9':
        menu_download()  # 進入下載選單
      case _:
        log().warning('找不到選項，請重新輸入！')


def menu_download():
  """
  下載選單
  :return:
  """
  print('\n◎ 本程式功能：自動下載案件檔案'
        '\n△ 注意事項：'
        '\n1. 執行前請確認「database」檔案已關閉。'
        '\n2. 下載後的檔案會儲存在「download」資料夾中。'
        '\n3. 執行到已下載過之案件時會自動跳過。'
        )
  check = input('是否確定開始下載？(Y/n)')

  if check.upper() == 'Y':
    download()


def menu_reply():
  print('\n◎ 本程式功能：從Excel檔讀取案件處理結果，逐一自動回覆'
        '\n△ 注意事項：'
        '\n1. 執行前請確認「database」檔案已關閉，以免無法儲存資料。'
        )
  input('輸入任意鍵繼續……')


def menu_get():
  print('\n◎ 本程式功能：透過網頁爬蟲，抓取每個檢舉案件的資訊，並儲存成Excel檔'
        '\n△ 注意事項：'
        '\n1. 執行前請確認「database」檔案已關閉，以免無法儲存資料。'
        '\n2. 執行到已抓取過之案件時會自動跳過。'
        )
  input('輸入任意鍵繼續……')


def menu_handle_lot():
  print('\n◎ 本程式功能：將所有案件符合搜尋條件的案件分派給指定人員'
        '\n△ 注意事項：'
        '\n1. 執行前請確認「database」檔案已關閉，以免無法儲存資料。'
        '\n2. 若要修改派出所及承辦人，請於「data」資料夾中的「setting」修改。'
        '\n3. 分派後會自動抓取該案件資料。'
        )
  input('輸入任意鍵繼續……')


def menu_handle_one():
  print('\n◎ 本程式功能：分派個別案件'
        '\n△ 注意事項：'
        '\n1. 執行前請確認「database」檔案已關閉，以免無法儲存資料。'
        '\n2. 若要修改派出所及承辦人，請於「data」資料夾中的「setting」修改。'
        '\n3. 請手動操作瀏覽器，進入「案件分派」頁面，並回到此程式輸入編號。'
        '\n4. 分派後會自動抓取該案件資料。'
        )
  input('輸入任意鍵繼續……')


def menu_data():
  """
  資料管理選單
  """
  while True:
    time.sleep(0.3)
    print('\n --------------------'
          '\n  ◎ 資料管理'
          '\n（1）匯出案件 Excel'
          '\n（2）從 Excel 匯入回填資料'
          '\n（0）返回上一頁'
          '\n --------------------'
          )
    mode = input('請選擇功能：')
    log().debug(f'已選擇資料管理功能{mode}')

    match mode:
      case '0':
        break
      case '1':
        export_cases_to_excel()
      case '2':
        print('\n◎ 本程式功能：從匯出的 Excel 中讀取回填資料並更新至資料庫'
              '\n△ 注意事項：'
              '\n1. 請選擇先前從本程式匯出的 Excel 檔案。'
              '\n2. 僅更新已填入「輸入簡碼」（P欄）的列。'
              '\n3. 比對依據為案號（A欄），找不到對應案號的列會被略過。'
              )
        input('輸入任意鍵繼續……')
        import_reply_fields_from_excel()
      case _:
        log().warning('找不到選項，請重新輸入！')
