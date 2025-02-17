import json


class Case:
  """
  取得的案件內容轉化為物件
  """

  def __init__(self, case_number, url, car, place, content, sender, time_all, undertaker, files: list):
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
  def __init__(self, case_number, car, url, sender, undertaker,  article, fine_number, reject_answer, select_code, status_code):
    self.number = case_number  # 案件編號
    self.car = car  # 車號
    self.url = url.replace('Details', 'Reply')  # 案件網址，替換成回覆用的網址
    self.sender = sender  # 檢舉人
    self.undertaker = undertaker[-3:]  # 承辦人姓名（取最後三個字）
    self.fine = fine_number  # 舉發單號
    self.article = article  # 舉發法條
    self.reject_answer = reject_answer  # 不舉發離由
    self.select = select_code  # 選項碼
    self.status = status_code  # 處理碼

  def values(self) -> list:
    return [self.number, self.car, self.url,self.sender, self.fine, self.article, self.reject_answer,
            self.select, self.status]

