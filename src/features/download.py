import os
import time
import requests
import json
from contextlib import closing
from src.utils.log import log
from src.utils.excel import load_excel, save_excel
from src.object.options import get_option

option = get_option()


# 主程式
def download():
  log().debug('「下載」開始執行')

  wb = load_excel('database')
  ws = wb['Todo']

  max_row = ws.max_row

  for row in range(2, max_row + 1):

    log().info(f'執行第 {row - 1} / {max_row - 1} 案')

    case_number = ws.cell(row, 1).value
    car = ws.cell(row, 2).value
    file_links = json.loads(ws.cell(row, 12).value)
    dl_status = ws.cell(row, 20).value

    if dl_status == 1:
      # 如果已經下載，跳過，且不記錄Log
      # log().info(f'案件「{case_number}」案已下載，略過')
      print(f'案件「{case_number}」案已下載，略過')
      continue

    download_single_case(case_number, car, file_links)

    ws.cell(row, 20).value = 1  # 更改下載碼
    save_excel(wb, 'database')

  log().info('「下載」執行完畢')
  time.sleep(0.5)
  input('輸入任意鍵繼續……')


# 函式：下載檔案
def download_single_case(case_number, car, links):
  """
  下載單一案件的檔案
  :param case_number:
  :param car:
  :param links:
  :return:
  """
  log().info(f'開始下載「{case_number}」之檔案……')
  folder = rf'.\download\{case_number}_{car}'
  try:
    os.mkdir(folder)
  except FileExistsError:
    pass
  for index, url in enumerate(links):
    file_name = url.split("/")[-1:][0]
    log().debug(f'{file_name} 開始下載')
    path = f'{folder}/{file_name}'  # 檔案路徑
    # if option.qrcode:
    #   make_qrcode(url, path)  # 如果選項開啟，則製作QRcode
    download_times = 0  # 嘗試下載次數
    while True:
      # try:
      progress = download_file(url, path)
      if progress == 100:
        log().info(f'{file_name} 下載成功({index}/{len(links)})')
        break
      if option.download_limit == download_times:
        log().error(f'{file_name} 下載嘗試次數已達上限，跳過本檔案，請手動下載。')
        break
      else:
        download_times += 1
        log().error('下載內容不完整，重新開始下載。')
      # except:
      #   log().warning(f'{file_name} 下載失敗，重新開始下載。', exc_info=True)
  log().info(f'「{case_number}」所有檔案下載完畢')


def download_file(url, path):
  file_name = os.path.basename(path)
  with closing(requests.get(url, timeout=10, verify=False, stream=True)) as response:
    chunk_size = 1024  # 單次請求最大值
    content_size = int(response.headers['content-length'])  # 檔案總大小
    data_count = 0  # 已下載大小
    print(f'{chunk_size},{content_size},{data_count}')
    with open(path, "wb") as file:
      for data in response.iter_content(chunk_size=chunk_size):
        file.write(data)
        done_block = int(data_count / content_size * 50)  # 已下載大小*方塊
        data_count = data_count + len(data)  # 實時進度條
        progress = data_count / content_size * 100  # %% 表示%
        print("\r %s [%s%s] %d%% " % (
          file_name + "：", done_block * '█', ' ' * (50 - 1 - done_block), progress), end=" ")
  return progress


# def make_qrcode(url, path):
#   img = qrcode.make(url)
#   img.save(f'{path}.png')
