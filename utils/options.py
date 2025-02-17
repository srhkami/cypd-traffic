import pandas as pd
import os
from utils.log import log
from utils.excel import dict_to_list

"""
跟設定選項有關的程式碼
"""

class Setting:
  def __init__(self, text):
    self.text = text,


class Option:
  def __init__(self, check, car, article, text_y, text_n, re_download, qr_code):
    self.check = True if check == '開啟' else False
    self.car = True if car == '開啟' else False
    self.article = True if article == '開啟' else False
    self.text_y = text_y
    self.text_n = text_n
    self.re_download = re_download
    self.qrcode = True if qr_code == '開啟' else False

  def values(self):
    return [self.check, self.car, self.article, self.text_y, self.text_n, self.re_download, self.qrcode]

def get_options() -> Option:
  """
  從setting之檔案內讀取相應內容
  :return: 設定的dict
  """
  excel = pd.read_excel(os.path.abspath(r'./data/setting.xlsx'), sheet_name='選項', index_col=0)  # 讀取設定檔
  col_name = '回覆案件設定'

  option = Option(
    check=excel.at['安全模式', col_name],
    car=excel.at['顯示車號', col_name],
    article=excel.at['顯示法條', col_name],
    text_y=excel.at['舉發回覆', col_name],
    text_n=excel.at['不舉發回覆', col_name],
    re_download=excel.at['重下載次數', col_name],
    qr_code=excel.at['生成QR', col_name],
  )

  log().debug('成功讀取選項')
  log().debug(option.values())
  return option


class Undertaker:
  def __init__(self, unit,name,code):
    self.unit = unit
    self.name = name
    self.code = code


def get_undertakers() -> dict:
  """
  讀取承辦人，並返回一個依各所代號查詢的字典
  :return:
  {
    10: Undertaker物件
  }
  """
  excel = pd.read_excel(os.path.abspath(r'.\data\setting.xlsx'), sheet_name='承辦人設定', index_col=0)
  undertakers = {}  # 承辦人的dict
  for i in range(0,len(excel.values)):
    undertakers[excel.index[i]] = Undertaker(
      unit=excel.values[i][0],
      name=excel.values[i][1],
      code=int(excel.values[i][2],)
    )
  log().debug('成功讀取承辦人設定')
  return undertakers


def select_undertaker() -> Undertaker:
  """
  :return: 承辦人資訊的dict
  """
  undertakers = get_undertakers()
  while True:
    x = int(input('請輸入分派對象：'))
    undertaker = undertakers.get(x)
    if undertaker:
      return undertaker
    else:
      log().error('輸入錯誤，請重新輸入！', exc_info=True)
