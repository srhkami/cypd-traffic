import json


class Case:
  """
  取得的案件內容轉化為物件
  """

  def __init__(self, case_number, url, car, place, content, sender, time_all, undertaker, files):
    self.number = case_number  # 案號
    self.car = car  # 車號
    self.url = url  # 案件的網址
    self.place = place  # 違規地點
    self.content = content  # 違規內容
    self.sender = sender  # 檢舉人
    self.time_all = time_all  # 違規日期
    self.undertaker = undertaker  # 承辦人
    self.yy = str(int(time_all[0:4]) - 1911)
    self.mm = time_all[5:7]
    self.dd = time_all[8:10]
    self.hr = time_all[11:13]
    self.min = time_all[14:16]
    self.files = json.dumps(files)  # 將檔案清單轉為json

  def values(self) -> list:
    return [self.number, self.car, self.url, self.place, self.content, self.sender,
            self.yy, self.mm, self.dd, self.hr, self.min, self.files, self.undertaker]


class CaseReply:
  def __init__(self, case_number, car, url, article, fine_number, reject_answer, select_code,  status_code):
    self.number = case_number
    self.car = car
    self.url = url
    self.fine_number = fine_number
    self.article = article
    self.reject_answer = reject_answer
    self.select = select_code
    self.status = status_code
