tags = {
  '信箱模組': '/html[1]/body[1]/div[2]/div[1]/ul[1]/li[1]/div[1]/a[1]',
  '交通違規信箱': '/html[1]/body[1]/div[2]/div[1]/ul[1]/li[1]/div[1]/ul[1]/li[4]/a[1]',
  # 以下在清單頁面
  '分派按鈕': '/html[1]/body[1]/div[2]/div[2]/div[1]/section[1]/table[1]/tbody[1]/tr[2]/td[13]/a[1]',
  # 以下是在詳情頁面
  '案號': '/html[1]/body[1]/div[2]/div[2]/div[1]/section[1]/fieldset[1]/table[1]/tbody[1]/tr[1]/td[1]',
  '車牌': '/html[1]/body[1]/div[2]/div[2]/div[1]/section[1]/fieldset[1]/table[2]/tbody[1]/tr[1]/td[2]',
  '地點': '/html[1]/body[1]/div[2]/div[2]/div[1]/section[1]/fieldset[1]/table[1]/tbody[1]/tr[2]/td[1]',
  '內容': '/html[1]/body[1]/div[2]/div[2]/div[1]/section[1]/fieldset[1]/table[1]/tbody[1]/tr[3]/td[1]',
  '檢舉人': '/html[1]/body[1]/div[2]/div[2]/div[1]/section[1]/fieldset[1]/table[1]/tbody[1]/tr[4]/td[1]',
  '違規日期': '/html[1]/body[1]/div[2]/div[2]/div[1]/section[1]/fieldset[1]/table[2]/tbody[1]/tr[1]/td[1]',

}  # 網頁標籤的Xpath路徑


def tag_td_undertaker(tr: int) -> str:
  """
  取得案件編號
  :return:
  """
  return f'/html[1]/body[1]/div[2]/div[2]/div[1]/section[1]/table[1]/tbody[1]/tr[{tr}]/td[11]'


def tag_a_detail(tr: int) -> str:
  """
  案件詳情的連結（用來點擊）
  :return:
  """
  return f'/html[1]/body[1]/div[2]/div[2]/div[1]/section[1]/table[1]/tbody[1]/tr[{tr}]/td[2]/a[1]'


def tag_a_assign(tr: int) -> str:
  """
  案件詳情的連結（用來點擊）
  :return:
  """
  return f'/html[1]/body[1]/div[2]/div[2]/div[1]/section[1]/table[1]/tbody[1]/tr[{tr}]/td[2]/a[1]'


def tag_a_file(li):
  """
    案件附檔的位置
    :return:
    """
  return f'/html[1]/body[1]/div[2]/div[2]/div[1]/section[1]/fieldset[1]/table[2]/tbody[1]/tr[3]/td[1]/li[{li}]/a[1]'