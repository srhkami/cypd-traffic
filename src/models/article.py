from pydantic import BaseModel
from src.utils import db
from src.utils.log import log


class Article(BaseModel):
  code: int
  text: str


def get_articles() -> dict[int, Article]:
  """
  讀取法條對照表，回傳依簡碼查詢法條的字典
  :return: {30102: Article物件}
  """
  rows = db.get_articles_raw()
  articles = {row['input_key']: Article(code=row['code'], text=row['text']) for row in rows}
  log().debug('成功讀取法條對應表')
  return articles
