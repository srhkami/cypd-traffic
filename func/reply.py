from src.utils.options import get_options, get_undertakers, get_articles
from src.utils.log import log
from src.utils.excel import load_excel, save_excel
from src.obj.case import CaseReply
from src.web.webdriver import get_intranet_headers
from src.web.request import ReplyPostData
from func.get import handle_case, get_case_detail
import requests
import pprint

option = get_options()  # 讀取Excel中的設定值
undertakers = get_undertakers()
articles = get_articles()


def reply(station_mode: bool = True):
  """
    執行回覆的主程式
    :param station_mode: 是否為派出所模式
    :return: 無
    """
  log().debug('「回覆」開始執行')

  wb = load_excel('database')
  ws = wb['Todo']

  headers = get_intranet_headers()  # 開啟瀏覽器取得標頭

  max_row = ws.max_row  # 取得最大列數
  for row in range(2, max_row + 1):
    # 逐一執行案件

    reply_case = CaseReply(ws, row)  # 建立案件物件

    reply_post = ReplyPostData(reply_case, option)
    post_data = reply_post.post_data()  # 取得Post的資料

    log().info(f'執行案件 {reply_case.number} ( {row - 1} / {max_row - 1} )')
    log().debug(reply_case.to_dict())

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

    if reply_case.input == 100 and not case.reject_answer:
      # 如果未舉發，但未輸入理由
      log().error(f'【{reply_case.number}】未填「不舉發理由」，請修正')
      continue

    if reply_case.input not in articles.keys():
      # 條款簡碼錯誤
      log().error(f'【{reply_case.number}】條款簡碼填寫錯誤，請修正')
      continue

    if (reply_case.input != 0 and reply_case.input != 100) and not reply_case.fine:
      # 如果舉發但未輸入單號或法條為空
      log().error(f'【{reply_case.number}】未填「舉發單號」，請修正')
      continue

    if not station_mode and reply_case.undertaker != undertakers.get(10).name:
      # 如果是分局模式，偵測到承辦人不同時，自動重新分派
      handle_case(reply_case.detail_url, undertakers.get(10), headers)

    if option.check:
      # 如果是安全模式，再次確認回覆文字
      print('\n───────案件再次確認────────')
      pprint.pprint(reply_case.to_dict())
      print('\n')
      print(post_data.get('Memo'))
      check = input('\n△ 是否確定回覆？（Y/n）')
      if check.upper() != 'Y':
        log().error(f'【{reply_case.number}】取消回覆')
        continue

    post_reply(ws.cell(row, 13), ws.cell(row, 14), reply_case, headers, post_data)

    save_excel(wb, 'database')

  log().info('「回覆」執行完畢')


def post_reply(undertaker_cell, status_cell, reply_case: CaseReply, headers, post_data):
  """
  使用post方法回覆
  :param status_cell: 狀態碼儲存格
  :param reply_case: 案件的物件
  :param headers: POST標頭
  :param post_data: POST資料
  :return:
  """
  requests.post(url=reply_case.reply_url, headers=headers, data=post_data)

  new_case = get_case_detail(detail_url=reply_case.detail_url, headers=headers)  # 再次抓取案件詳情

  if new_case.status == '已結案':
    status_cell.value = new_case.status  # 更改處理碼為「已結案」
    undertaker_cell.value = new_case.undertaker
    log().info(f'【{new_case.number}】回覆成功')
  else:
    log().error(f'【{new_case.number}】回覆失敗')
