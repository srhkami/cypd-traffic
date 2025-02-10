import pandas as pd
import os
from utils.log import log

"""
跟設定選項有關的程式碼
"""


class Option:
  def __init__(self, text_y, text_n, name, car, article, re_download, qr_code):
    self.text_y = text_y,
    self.text_n = text_n,
    self.name = True if name == '開啟' else False,
    self.car = True if car == '開啟' else False,
    self.article = True if article == '開啟' else False,
    self.re_download = re_download,
    self.qrcode = True if qr_code == '開啟' else False,


def get_options() -> Option:
  """
  從setting之檔案內讀取相應內容
  :return: 設定的dict
  """
  excel = pd.read_excel(os.path.abspath(r'./data/setting.xlsx'), sheet_name='選項', index_col=0)  # 讀取設定檔
  col_name = '回覆案件設定'

  option = Option(
    text_y=excel.at['舉發回覆', col_name],
    text_n=excel.at['不舉發回覆', col_name],
    name=excel.at['顯示稱謂', col_name],
    car=excel.at['顯示車號', col_name],
    article=excel.at['顯示法條', col_name],
    re_download=excel.at['重下載次數', col_name],
    qr_code=excel.at['生成QR', col_name],
  )

  log().debug('成功讀取選項')
  return option


def get_person():
  """
  讀取承辦人
  :return:
  """
  excel = pd.read_excel(os.path.abspath(r'../data/setting.xlsx'), sheet_name='承辦人設定', index_col=0)
  return excel


def select_undertaker() -> dict:
  """
  :return: 承辦人資訊的dict
  """
  excel = get_person()
  while True:
    x = int(input('請輸入分派對象：'))
    if x in excel.index:
      undertaker = {
        'name': excel.loc[x, '承辦人'],
        'unit': excel.loc[x, '單位'],
        'code': int(excel.loc[x, '代號'])
      }
      return undertaker
    else:
      log().error('輸入錯誤，請重新輸入！', exc_info=True)


if __name__ == '__main__':
  excel = get_person()
  print((excel.index))

  i = input(':')
  i = int(i)
  if i in excel.index:
    print(True)
  else:
    print(False)
