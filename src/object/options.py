import pandas as pd
import os
from pydantic import BaseModel, field_validator
from src.utils.log import log

"""
跟設定選項有關的程式碼
"""


class Option(BaseModel):
  """
  程式的設定物件
  """
  check: bool
  car: bool
  article: bool
  text_y: str
  text_n: str
  download_limit: int

  @field_validator('check', 'car', 'article', mode='before')
  @classmethod
  def parse_kaizhi(cls, v):
    if isinstance(v, str):
      return v == '開啟'
    return v


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
  log().debug(option.model_dump())
  return option
