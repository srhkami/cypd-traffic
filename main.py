import time
# from utils import assign, download, get, reply
from utils.log import log
from utils.excel import load_excel, save_excel, readonly_excel
from utils.webdriver import open_browser
from static.info import ver, changelog
from static.menu import intro, menu_main, menu_station, menu_precinct, menu_download

# 主程式
if __name__ == '__main__':
  log().debug('！----- 程式開始執行 -----！')
  log().debug(f'程式版本：{ver}')

  intro()  # 顯示歡迎介面
  input('輸入任意鍵繼續……')

  # 主程式開始
  while True:
    time.sleep(0.3)
    mode = menu_main()  # 主選單，選擇模式
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
      case '123':
        # 貼上網址會有雙引號，故先移除
        url = str(input('請輸入指定網址：')).replace('"', '')
        # url = url_test
        log().info('已啟用測試網址')
      case '0':
        log().debug('程式已結束')
        exit()
      case _:
        print('輸入錯誤，請重新輸入！')
