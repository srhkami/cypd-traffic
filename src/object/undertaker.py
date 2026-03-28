import pandas as pd
import os
from pydantic import BaseModel
from src.utils.log import log


class Undertaker(BaseModel):
  """
  承辦人
  """
  unit: str
  name: str
  code: int


def get_undertakers() -> dict[int, Undertaker]:
  """
  讀取承辦人，並返回一個依各所代號查詢的字典
  :return:
  {
    10: Undertaker物件
  }
  """
  excel = pd.read_excel(os.path.abspath(r'.\data\setting.xlsx'), sheet_name='承辦人設定', index_col=0)
  undertakers = {}  # 承辦人的dict
  for i in range(0, len(excel.values)):
    undertakers[excel.index[i]] = Undertaker(
      unit=excel.values[i][0],
      name=excel.values[i][1],
      code=int(excel.values[i][2], )
    )
  log().debug('成功讀取承辦人設定')
  return undertakers


def select_undertaker() -> Undertaker:
  """
  :return: 承辦人資訊的dict
  """
  undertakers = get_undertakers()
  while True:
    x = int(input('請輸入分派對象：'))
    undertaker: Undertaker = undertakers.get(x)
    if undertaker:
      log().info(f'已選擇 {undertaker.unit}-{undertaker.name}')
      check = input('是否確定承辦人？(Y/n)')
      if check.upper() == 'Y':
        return undertaker
      else:
        continue
    else:
      log().error('輸入錯誤，請重新輸入！', exc_info=True)
