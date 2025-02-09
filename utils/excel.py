import openpyxl
import pandas as pd
import os
from utils.log import log

# 用 openpyxl 開啟Excel檔，用以編輯Excel
def load_excel(file):
  try:
    wb = openpyxl.load_workbook(os.path.abspath(rf'.\data\{file}.xlsx'))
    log().info(f'已從Excel檔「{file}」載入資料')
    return wb
  except:
    log().critical('無法取得資料，請檢查excel檔名、位置是否正確！', exc_info=True)


# 用 openpyxl 儲存Excel
def save_excel(wb, file):
  while True:
    try:
      wb.save(os.path.abspath(rf'.\data\{file}.xlsx'))
      log().info(f'儲存Excel檔成功，檔名為「{file}」')
      break
    except:
      log().error(f'儲存Excel檔失敗，請檢查「{file}」檔案是否已關閉！', exc_info=True)
      print('輸入任意鍵重試……')


#  用 pndas 讀取Excel檔資料，輸出為字典檔
def readonly_excel(file):
  try:
    df = pd.read_excel(os.path.abspath(rf'.\data\{file}.xlsx'), sheet_name='ToDo')
    log().info(f'已從Excel檔「{file}」取得資料')
    log().debug(df)
    return df
  except:
    log().critical('無法取得資料，請檢查excel檔名、位置是否正確！', exc_info=True)
    print('輸入任意鍵離開……')

def dict_to_list(df):
  """
  讀取Output檔後的字典，轉置為清單型式
  :param df:
  :return:
  """
  """
      由以下結構：
      {
        '案件編號': [
          202411060089,
          202411060139
        ],
        '違規車號': [
          'BDD-1602',
          'AVU-3369'
        ],
        '案件標題': [
          '民雄鄉建國路二段142號前路口',
          '民雄鄉台一線南向262.4公里處'
        ],
        轉化為：
          [
            {
              '案件編號': '202411060089',
              '違規車號': 'BDD-1602',
              '案件標題': '民雄鄉建國路二段142號前路口',
            },
            {
              '案件編號': '202411060139',
              '違規車號': 'AVU-3369',
              '案件標題': '民雄鄉台一線南向262.4公里處',
            },
          ]
    """
  case_list = df.T.to_dict().values()
  return case_list
  # obj_list = []
  # for case in case_list:
  #   obj_list.append(Case(case=case))
  # return obj_list


if __name__ == '__main__':
  df = readonly_excel('database')
