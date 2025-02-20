from utils.options import get_options, get_undertakers, get_articles
from utils.log import log
from utils.excel import load_excel, save_excel
from static.case import CaseReply
from utils.webdriver import get_intranet_headers, ReplyPostData
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

    case = CaseReply(ws, row)  # 建立案件物件

    post_data = ReplyPostData(case, option).post_data()  # 取得Post的資料

    log().info(f'執行案件 {case.number} ( {row - 1} / {max_row - 1} )')
    log().debug(case.to_dict())

    if case.status == '已結案':
      # 如果該案已結案，跳過
      log().error(f'【{case.number}】已結案，不予執行')
      continue

    if case.input == 0:
      # 如果該案未輸入處理結果，跳過
      log().error(f'【{case.number}】未處理，不予執行')
      continue

    if case.input == 100 and station_mode:
      # 如果未舉發，但是派出所模式
      log().error(f'【{case.number}】不舉發，派出所模式不予執行')
      continue

    if case.input == 100 and not case.reject_answer:
      # 如果未舉發，但未輸入理由
      log().error(f'【{case.number}】未填「不舉發理由」，請修正')
      continue

    if case.input not in articles.keys():
      # 條款簡碼錯誤
      log().error(f'【{case.number}】條款簡碼填寫錯誤，請修正')
      continue

    if (case.input != 0 and case.input != 100) and not case.fine:
      # 如果舉發但未輸入單號或法條為空
      log().error(f'【{case.number}】未填「舉發單號」，請修正')
      continue

    if not station_mode and case.undertaker != undertakers.get(10).name:
      # 如果是分局模式，偵測到承辦人不同時，自動重新分派
      status_code = handle_case(case.detail_url, undertakers.get(10), headers)
      if status_code == 200:
        log().info(f'重新分派成功')
      else:
        log().warning(f'重新分派失敗，跳過本案。錯誤碼：{status_code}')
        continue

    if option.check:
      # 如果是安全模式，再次確認回覆文字
      print('───────案件再次確認────────')
      pprint.pprint(case.to_dict())
      print('\n')
      print(post_data.get('Memo'))
      check = input('△ 是否確定回覆？（Y/n）')
      if check.upper() != 'Y':
        log().error(f'【{case.number}】取消回覆')
        continue

    post_reply(ws.cell(row, 14), case, headers, post_data)

    save_excel(wb, 'database')

  log().info('「回覆」執行完畢')


def post_reply(status_cell, case: CaseReply, headers, post_data):
  """
  使用post方法回覆
  :param status_cell: 狀態碼儲存格
  :param case: 案件的物件
  :param headers: POST標頭
  :param post_data: POST資料
  :return:
  """
  requests.post(url=case.reply_url, headers=headers, data=post_data)

  case = get_case_detail(detail_url=case.detail_url, headers=headers)  # 再次抓取案件詳情

  if case.status == '已結案':
    status_cell.value = case.status  # 更改處理碼為「已結案」
    log().info(f'【{case.number}】回覆成功')
  else:
    log().error(f'【{case.number}】回覆失敗')
