from utils.options import get_options
from utils.log import log
from utils.webdriver import open_browser, fx
from utils.excel import load_excel, save_excel
from static.case import CaseReply
from selenium.webdriver.support.ui import Select

if __name__ == '__main__':
  option = get_options()  # 讀取Excel中的設定值

  wb = load_excel('database')
  ws = wb['ToDo']

  max_row = ws.max_row

  for row in range(2, max_row + 1):

    case = CaseReply(
      case_number=ws.cell(row, 1).value,  # 案號
      car=ws.cell(row, 2).value,  # 車號
      url=ws.cell(row, 3).value.replace('Details', 'Reply'),  # 回覆的網址
      article=ws.cell(row, 17).value,  # 舉發條款
      fine_number=ws.cell(row, 18).value,  # 舉發單號
      reject_answer=ws.cell(row, 19).value,  # 不舉發理由
      select_code=ws.cell(row, 20).value,  # 選項碼
      status_code=ws.cell(row, 21).value,  # 狀態碼
    )  # 建立案件物件

    print(f'執行案件 {case.number} ( {row - 1} / {max_row - 1} )')
    print(case.values())

    if case.status == 2:
      # 如果該案已結案，跳過
      log().error(f'【{case.number}】已結案，不予執行')
      continue

    if case.select == 0:
      # 如果該案未輸入處理結果，跳過
      log().error(f'【{case.number}】未處理，不予執行')
      continue

    if case.select == 100 and not case.reject_answer:
      # 如果未舉發，但未輸入理由
      log().error(f'【{case.number}】未填「不舉發理由」，請修正')
      continue

    if (case.select != 0 and case.select != 100) and (not case.fine_number or not case.article):
      # 如果舉發但未輸入單號或法條為空
      log().error(f'【{case.number}】未填「舉發單號」，請修正')
      continue

    print('正常，已舉發。')
