import pandas as pd
import os
from src.utils.log import log

"""
跟設定選項有關的程式碼
"""


class Option:
  """
  程式的設定物件
  """
  def __init__(self, check, car, article, text_y, text_n, download_limit):
    self.check = True if check == '開啟' else False
    self.car = True if car == '開啟' else False
    self.article = True if article == '開啟' else False
    self.text_y = text_y
    self.text_n = text_n
    self.download_limit = int(download_limit)

  def values(self):
    return [self.check, self.car, self.article, self.text_y, self.text_n, self.download_limit]

  def to_dict(self):
    option_dict = {
      '安全模式': self.check,
      '顯示車號': self.car,
      '顯示法條': self.article,
      '舉發回覆': self.text_y,
      '不舉發回覆': self.text_n,
      '下載上限': self.download_limit,
    }
    return option_dict


def get_option() -> Option:
  """
  從setting之檔案內讀取相應內容
  :return: 設定的物件
  """
  excel = pd.read_excel(os.path.abspath(r'./data/setting.xlsx'), sheet_name='選項', index_col=0)  # 讀取設定檔
  col_name = '回覆案件設定'

  option = Option(
    check=excel.at['安全模式', col_name],
    car=excel.at['顯示車號', col_name],
    article=excel.at['顯示法條', col_name],
    text_y=excel.at['舉發回覆', col_name],
    text_n=excel.at['不舉發回覆', col_name],
    download_limit=excel.at['重下載次數', col_name],
  )

  log().debug('成功讀取選項')
  log().debug(option.values())
  return option
