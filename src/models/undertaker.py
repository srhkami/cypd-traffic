from pydantic import BaseModel
from src.utils import db
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
  讀取承辦人，回傳依各所代號查詢的字典
  :return: {10: Undertaker物件}
  """
  rows = db.get_undertakers_raw()
  undertakers = {
    row['station_id']: Undertaker(unit=row['unit'], name=row['name'], code=row['code'])
    for row in rows
  }
  log().debug('成功讀取承辦人設定')
  return undertakers


def select_undertaker() -> Undertaker:
  """
  互動式選擇承辦人
  :return: 承辦人資訊
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
