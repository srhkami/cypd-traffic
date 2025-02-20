from utils.options import get_options, get_undertakers
from utils.log import log
from utils.excel import load_excel, save_excel
from static.case import CaseReply
from utils.webdriver import get_intranet_headers, ReplyPostData
from func.get import handle_case
import requests

option = get_options()  # 讀取Excel中的設定值
undertakers = get_undertakers()


def reply(station_mode: bool = True):
  """
    執行回覆的主程式
    :param station_mode: 是否為派出所模式
    :return: 無
    """
  log().debug('「回覆」開始執行')

  wb = load_excel('database')
  ws = wb['ToDo']
  wb_read = load_excel('database', data_only=True)
  ws_read = wb_read['ToDo']

  headers = get_intranet_headers()  # 開啟瀏覽器取得標頭

  max_row = ws_read.max_row  # 取得最大列數
  for row in range(2, max_row + 1):
    # 逐一執行案件

    case = CaseReply(
      case_number=ws_read.cell(row, 1).value,  # 案號
      car=ws_read.cell(row, 2).value,  # 車號
      url=ws_read.cell(row, 3).value,  # 網址
      sender=ws_read.cell(row, 6).value,  # 檢舉人
      undertaker=ws_read.cell(row, 13).value,  # 承辦人
      article=ws_read.cell(row, 17).value,  # 舉發條款
      fine_number=ws_read.cell(row, 18).value,  # 舉發單號
      reject_answer=ws_read.cell(row, 19).value,  # 不舉發理由
      select_code=ws_read.cell(row, 20).value,  # 選項碼
      status_code=ws_read.cell(row, 21).value,  # 狀態碼
    )  # 建立案件物件

    post = ReplyPostData(case, option)
    post_data = post.post_data()

    log().info(f'執行案件 {case.number} ( {row - 1} / {max_row - 1} )')
    log().debug(case.values())

    if case.status == 2:
      # 如果該案已結案，跳過
      log().error(f'【{case.number}】已結案，不予執行')
      continue

    if case.select == 0:
      # 如果該案未輸入處理結果，跳過
      log().error(f'【{case.number}】未處理，不予執行')
      continue

    if case.status == 100 and station_mode:
      # 如果未舉發，但是派出所模式
      log().error(f'【{case.number}】不舉發，派出所模式不予執行')
      continue

    if case.select == 100 and not case.reject_answer:
      # 如果未舉發，但未輸入理由
      log().error(f'【{case.number}】未填「不舉發理由」，請修正')
      continue

    if (case.select != 0 and case.select != 100) and (not case.fine or not case.article):
      # 如果舉發但未輸入單號或法條為空
      log().error(f'【{case.number}】未填「舉發單號」，請修正')
      continue

    if not station_mode and case.undertaker != undertakers.get(10).name:
      # 如果是分局模式，偵測到承辦人不同時，自動重新分派
      status_code = handle_case(case.url, undertakers.get(10), headers)
      if status_code == 200:
        log().info(f'重新分派成功')
      else:
        log().warning(f'重新分派失敗，跳過本案。錯誤碼：{status_code}')
        continue

    if option.check:
      # 如果是安全模式，再次確認回覆文字
      print(post_data.get('Memo'))
      check = input('△ 是否確定回覆？（Y/n）')
      if check.upper() != 'Y':
        log().error(f'【{case.number}】取消回覆')
        continue

    post_reply(ws.cell(row, 21), case, headers, post_data)

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
  res = requests.post(url=case.url, headers=headers, data=post_data)
  log().debug(res)
  if res.status_code == 200:
    status_cell.value = 2  # 更改處理碼為「結案」
    log().info(f'【{case.number}】回覆成功！')
  else:
    log().error(f'【{case.number}】使用 POST 方法回覆失敗，錯誤碼：{res.status_code}')

# def reply_every(browser, status_cell, case: CaseReply, setting_re: bool, setting_ck: bool):
#   """
#   回覆個別案件
#   :param browser: 瀏覽器
#   :param case: 案件詳情物件
#   :param setting_re: 是否重新分派
#   :param setting_ck: 是否再次確認
#   :return:
#   """
#   browser.get(case.url)
#
#   if setting_re:
#     pass  # 重新分派案件預留
#
#   input_values(browser, case)
#   reply_submit(browser, status_cell, case, setting_ck)
#
#
# # 函式：填入回覆資訊
# def input_values(browser, case: CaseReply):
#   """
#   填入回覆資訊
#   :param browser:
#   :param case: 案件的物件
#   :return:
#   """
#   try:
#     # name = fx(browser,
#     #           '/html[1]/body[1]/div[2]/div[2]/div[1]/section[1]/fieldset[1]/table[1]/tbody[1]/tr[4]/td[1]').text
#     # first_name = name[0]  # 取得姓氏
#
#     # no_text = str(case.number)
#     # date = f'{int(no_text[0:4]) - 1911}年{no_text[4:6]}月{no_text[6:8]}日'
#     # car = fx(browser, '/html[1]/body[1]/div[2]/div[2]/div[1]/section[1]/fieldset[1]/table[2]/tbody[1]/tr[1]/td[2]').text
#
#     reply_text = ''  # 回覆文字
#     if option.name:
#       reply_text += f'{case.sender[0]}先生/小姐您好，'
#     reply_text += '您於本縣警察局交通違規檢舉專區檢舉違規案件，經處理後茲答覆如下：'
#
#     if case.select == 100:
#       # 不舉發的情況
#       log().debug('本案為不舉發')
#       reply_text += f'\n{case.reject_answer}'  # 加入不舉發回覆
#       reply_text += option.text_n  # 加入罐頭訊息
#       Select(
#         fx(browser, '/html[1]/body[1]/div[2]/div[2]/div[1]/section[1]/form[1]/div[8]/select[1]')).select_by_index(
#         1)  # 選擇「不舉發」
#       Select(
#         fx(browser,
#            '/html[1]/body[1]/div[2]/div[2]/div[1]/section[1]/form[1]/div[9]/div[2]/select[1]')).select_by_index(
#         12)  # 選擇不舉發理由：「其他」
#
#     else:
#       # 舉發的情況
#       log().debug('本案為舉發')
#
#       if option.car:  # 加入違規車號
#         reply_text += f'違規車號： {case.car}。\n'
#
#       if option.article:  # 加入舉發法條
#         reply_text += f'舉發法條： {case.article} 。\n'
#
#       reply_text += option.text_y  # 加入罐頭訊息
#       Select(
#         fx(browser, '/html[1]/body[1]/div[2]/div[2]/div[1]/section[1]/form[1]/div[8]/select[1]')).select_by_index(
#         0)  # 選擇「舉發」
#       fx(browser, '/html[1]/body[1]/div[2]/div[2]/div[1]/section[1]/form[1]/div[10]/div[2]/input[1]').send_keys(
#         case.fine)  # 貼上舉發單號
#       Select(
#         fx(browser, '/html[1]/body[1]/div[2]/div[2]/div[1]/section[1]/form[1]/div[10]/div[2]/'
#                     'select[1]')).select_by_value(str(case.select))  # 選擇舉發項目」
#
#     fx(browser, '/html[1]/body[1]/div[2]/div[2]/div[1]/section[1]/form[1]/div[2]/textarea[1]').send_keys(
#       reply_text)  # 貼上回覆訊息
#     log().debug('回覆訊息填入完成')
#     Select(fx(browser, '/html[1]/body[1]/div[2]/div[2]/div[1]/section[1]/form[1]/div[6]/select[1]')).select_by_index(
#       0)  # 選擇「結案」
#
#   except:
#     log().warning('填入回覆資訊失敗', exc_info=True)
#
#
# def reply_submit(browser, status_cell, case: CaseReply, setting_ck):
#   """
#   再次確認是否觸發安全模式
#   :param browser:
#   :param status_cell: 處理碼的儲存格
#   :param case:
#   :param setting_ck: 是否再次確認
#   :return:
#   """
#   if setting_ck == 'Y':
#     # 再次確認才決定是否回覆
#     recheck = input('請檢查回覆內容，是否確定送出？(Y/n)')
#     if recheck.upper() != 'Y':
#       # 如果並非輸入Y，取消回覆
#       log().info(f'{case.number} 回覆已取消')
#       return
#
#   fx(browser, '/html[1]/body[1]/div[2]/div[2]/div[1]/section[1]/form[1]/p[1]/input[1]').click()  # 點擊回覆按鈕
#   log().info(f'【{case.number}】回覆成功！')
#   status_cell.value = 2  # 更改處理碼為「結案」
