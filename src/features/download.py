import os
import time
import requests
import json
from contextlib import closing
from src.utils.log import log
from src.object.options import get_option
from src.utils import db


# 主程式
def download():
  log().debug('「下載」開始執行')

  option = get_option()
  cases = db.get_all_cases()
  total = len(cases)

  for idx, row in enumerate(cases):
    case_number = row['number']
    car = row['car']
    file_links = json.loads(row['files_json'])
    dl_status = row['download_status']

    log().info(f'執行第 {idx + 1} / {total} 案')

    if dl_status == 1:
      # 如果已經下載，跳過
      print(f'案件「{case_number}」案已下載，略過')
      continue

    download_single_case(case_number, car, file_links, option.download_limit)

    db.update_case_download_status(case_number)

  log().info('「下載」執行完畢')
  time.sleep(0.5)
  input('輸入任意鍵繼續……')


# 函式：下載單一案件的所有檔案
def download_single_case(case_number, car, links, download_limit: int):
  """
  下載單一案件的檔案
  :param case_number:
  :param car:
  :param links:
  :param download_limit: 重試上限次數
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
    download_times = 0  # 嘗試下載次數
    while True:
      progress = download_file(url, path)
      if progress == 100:
        log().info(f'{file_name} 下載成功({index}/{len(links)})')
        break
      if download_limit == download_times:
        log().error(f'{file_name} 下載嘗試次數已達上限，跳過本檔案，請手動下載。')
        break
      else:
        download_times += 1
        log().error('下載內容不完整，重新開始下載。')
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
