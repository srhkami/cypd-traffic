from src.object.case import CaseReply
from src.object.options import Option
from src.object.article import get_articles
from src.utils.log import log

articles = get_articles()


class ReplyPostData:
  """
  回覆案件Post請求所需要的資料
  """
  def __init__(self, case: CaseReply, option: Option):
    self.case = case
    self.option = option

  def post_data(self) -> dict:

    reply_text = '您於本縣警察局交通違規檢舉專區檢舉違規案件，經處理後茲答覆如下：\n'  # 回覆文字

    if self.case.input == 100:
      # 不舉發的情況
      log().debug('本案為不舉發')
      reply_text += self.case.reject_answer  # 加入不舉發回覆
      reply_text += self.option.text_n  # 加入罐頭訊息

    else:
      # 舉發的情況
      log().debug('本案為舉發')

      if self.option.car:  # 加入違規車號
        reply_text += f'違規車號： {self.case.car}。\n'

      if self.option.article:  # 加入舉發法條
        reply_text += f'舉發法條： {articles[self.case.input].text} 。\n'

      reply_text += self.option.text_y  # 加入罐頭訊息

    reply_post_data = {
      'Memo': reply_text,
      'Status': '第一次回覆',
      'IsEnd': '是',
      'isReport': '否' if self.case.input == 100 else '是',
      'MailboxTrafficCatalogRejectId': 1,
      'MailboxTrafficArchiveTitle': self.case.fine,
      'MailboxTrafficCatalogBackgroundId': articles[self.case.input].code,
    }

    log().debug(reply_post_data)

    return reply_post_data
