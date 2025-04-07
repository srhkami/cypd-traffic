from utils.log import log
from static.info import ver
from static.menu import intro, menu_main

# 主程式
if __name__ == '__main__':
  log().debug('！----- 程式開始執行 -----！')
  log().debug(f'程式版本：{ver}')

  intro()  # 顯示歡迎介面
  input('輸入任意鍵繼續……')

  menu_main()
