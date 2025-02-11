from static.case import Case
from utils.excel import load_excel, save_excel
from openpyxl.styles import Font

if __name__ == '__main__':
  # get()
  wb = load_excel('database')  # 開啟Excel
  ws = wb['ToDo']

  case = Case(
    case_number='202501010001',
    url='http://127.0.0.1/',
    car='ABC-1234',
    place='地點',
    content='內容',
    sender='王曉明',
    time_all='2024/01/01 16:00',
    undertaker='王小白',
    files=['1','2']
  )

  ws.append(case.values() + [
    None,
    '=IF(U2=1,"已分派",IF(U2=2,"結案","處理中"))',
    0,
    '=VLOOKUP($P2,舉發法條!$A$2:$D$54,3,FALSE)',
    None,
    None,
    '=VLOOKUP($P2,舉發法條!$A$2:$D$54,2,FALSE)',
    1,
    0
  ])  # 新增案件

  # ws.font(Font(name='Microsoft JhengHei UI',size=10))

  save_excel(wb, 'database')
