import logging
import os

app_logger = logging.getLogger('app')
app_logger.setLevel(logging.DEBUG)
handler_print = logging.StreamHandler()
handler_txt = logging.StreamHandler(open(os.path.abspath(r'./data/debug.log'), 'a'))
handler_print.setLevel(logging.INFO)
handler_print.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
handler_txt.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(lineno)d - %(message)s'))
app_logger.addHandler(handler_print)
app_logger.addHandler(handler_txt)


def log():
  '''
  :return: 調用此函數，用來輸出或顯示記錄檔
  使用方法： log().error('下載內容不完整，重新開始下載。')
  '''
  return app_logger