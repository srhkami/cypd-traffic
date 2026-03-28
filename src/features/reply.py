from pydantic import BaseModel
from src.features.get import get_case_detail, assign_case_by_post
from src.models.article import get_articles, Article
from src.models.options import get_option, Option
from src.models.undertaker import get_undertakers
from src.utils.log import log
from src.models.case import CaseReply
from src.utils.webdriver import get_intranet_headers
from src.utils import db
import requests
import pprint


class ReplyPostPayload(BaseModel):
  """
  回覆案件 POST 請求的資料格式
  """
  Memo: str
  Status: str
  IsEnd: str
  isReport: str
  MailboxTrafficCatalogRejectId: int
  MailboxTrafficArchiveTitle: str
  MailboxTrafficCatalogBackgroundId: int


class ReplyPostData:
  """
  回覆案件Post請求所需要的資料
  """
  def __init__(self, case: CaseReply, option: Option, articles: dict[int, Article]):
    self.case = case
    self.option = option
    self.articles = articles

  def post_data(self) -> ReplyPostPayload:

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
        reply_text += f'舉發法條： {self.articles[self.case.input].text} 。\n'

      reply_text += self.option.text_y  # 加入罐頭訊息

    payload = ReplyPostPayload(
      Memo=reply_text,
      Status='第一次回覆',
      IsEnd='是',
      isReport='否' if self.case.input == 100 else '是',
      MailboxTrafficCatalogRejectId=13,
      MailboxTrafficArchiveTitle=self.case.fine if self.case.input != 100 else '',
      MailboxTrafficCatalogBackgroundId=self.articles[self.case.input].code if self.case.input != 100 else 53,
    )

    log().debug(payload)

    return payload


def reply(station_mode: bool = True, re_assign: bool = False):
  """
  執行回覆的主程式
  :param station_mode: 是否為派出所模式
  :param re_assign: 是否重新分派
  :return: 無
  """
  log().debug('「回覆」開始執行')

  option = get_option()
  undertakers = get_undertakers()
  articles = get_articles()

  cases = db.get_all_cases()
  headers = get_intranet_headers()  # 開啟瀏覽器取得標頭

  total = len(cases)
  for idx, row in enumerate(cases):
    reply_case = CaseReply.from_db_row(row)

    reply_post = ReplyPostData(reply_case, option, articles)
    post_data = reply_post.post_data()  # 取得Post的資料

    log().info(f'執行案件 {reply_case.number} ( {idx + 1} / {total} )')
    log().debug(reply_case.model_dump())

    if reply_case.status == '已結案':
      # 如果該案已結案，跳過
      log().error(f'【{reply_case.number}】已結案，不予執行')
      continue

    if reply_case.input == 0:
      # 如果該案未輸入處理結果，跳過
      log().error(f'【{reply_case.number}】未處理，不予執行')
      continue

    if reply_case.input == 100 and station_mode:
      # 如果未舉發，但是派出所模式
      log().error(f'【{reply_case.number}】不舉發，派出所模式不予執行')
      continue

    if reply_case.input == 100 and not reply_case.reject_answer:
      # 如果未舉發，但未輸入理由
      log().error(f'【{reply_case.number}】未填「不舉發理由」，請修正')
      continue

    if reply_case.input not in articles.keys():
      # 條款簡碼錯誤
      log().error(f'【{reply_case.number}】條款簡碼填寫錯誤，請修正')
      continue

    if (reply_case.input != 0 and reply_case.input != 100) and not reply_case.fine:
      # 如果舉發但未輸入單號
      log().error(f'【{reply_case.number}】未填「舉發單號」，請修正')
      continue

    if not station_mode and re_assign and reply_case.undertaker != undertakers.get(10).name:
      # 非派出所模式且開啟重新分派，且承辦人非分局承辦人 → 先重新分派
      assign_case_by_post(reply_case.detail_url, undertakers.get(10), headers)

    if option.check:
      # 如果是安全模式，再次確認回覆文字
      print('\n───────案件再次確認────────')
      pprint.pprint(reply_case.model_dump())
      print('\n')
      print(post_data.Memo)
      check = input('\n△ 是否確定回覆？（Y/n）')
      if check.upper() != 'Y':
        log().error(f'【{reply_case.number}】取消回覆')
        continue

    reply_by_post(reply_case.number, reply_case, headers, post_data)

  log().info('「回覆」執行完畢')


def reply_by_post(number: str, reply_case: CaseReply, headers, post_data):
  """
  使用post方法回覆，成功後更新資料庫狀態
  :param number: 案號
  :param reply_case: 案件的物件
  :param headers: POST標頭
  :param post_data: POST資料（ReplyPostPayload）
  :return:
  """
  requests.post(url=reply_case.reply_url, headers=headers, data=post_data.model_dump())

  check_case = get_case_detail(detail_url=reply_case.detail_url, headers=headers)  # 再次抓取案件詳情

  if check_case.status == '已結案':
    db.update_case_status(number, check_case.status, check_case.undertaker)
    log().info(f'【{check_case.number}】回覆成功')
  else:
    log().error(f'【{check_case.number}】回覆失敗')
