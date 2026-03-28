from src.utils.log import log
from src.ui.info import ver

# 關鍵：在所有其他模組 import 之前，先初始化資料庫
# menu.py 匯入的 reply.py、download.py 在模組層級會呼叫 get_option() 等函式，
# 因此資料庫必須在這些模組被載入前就已就緒。
from src.utils.db import init_db
init_db()

from src.ui.menu import intro, menu_main  # noqa: E402（必須在 init_db 之後）

# 主程式
if __name__ == '__main__':
  log().debug('！----- 程式開始執行 -----！')
  log().debug(f'程式版本：{ver}')

  intro()  # 顯示歡迎介面
  input('輸入任意鍵繼續……')

  menu_main()
