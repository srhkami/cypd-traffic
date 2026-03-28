from pydantic import BaseModel, field_validator
from src.utils import db
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
  從資料庫讀取系統選項
  :return: 設定的物件
  """
  rows = db.get_options_raw()
  opts = {row['key']: row['value'] for row in rows}

  option = Option(
    check=opts.get('check', '關閉'),
    car=opts.get('car', '關閉'),
    article=opts.get('article', '關閉'),
    text_y=opts.get('text_y', ''),
    text_n=opts.get('text_n', ''),
    download_limit=int(opts.get('download_limit', '3')),
  )

  log().debug('成功讀取選項')
  log().debug(option.model_dump())
  return option
