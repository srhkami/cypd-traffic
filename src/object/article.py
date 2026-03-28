import pandas as pd
import os
from pydantic import BaseModel
from src.utils.log import log


class Article(BaseModel):
  code: int
  text: str


def get_articles() -> dict[int, Article]:
  """
  讀取法條對照表，並返回一個依簡碼查詢法條的字典
  :return:
  {
    30102: Article物件
  }
  """
  excel = pd.read_excel(os.path.abspath(r'.\data\database.xlsx'), sheet_name='Article', index_col=0)
  articles = {}  # 承辦人的dict
  for i in range(0, len(excel.values)):
    articles[excel.index[i]] = Article(
      code=excel.values[i][0],
      text=excel.values[i][1],
    )
  log().debug('成功讀取法條對應表')
  return articles
