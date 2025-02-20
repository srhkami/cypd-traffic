import json


class Case:
  """
  取得的案件內容轉化為物件
  """

  def __init__(self, case_number, url, car, place, content, sender, time_all, undertaker, status, files: list):
    self.number = case_number  # 案號
    self.car = car  # 車號
    self.url = url  # 案件的網址
    self.place = place  # 違規地點
    self.content = content  # 違規內容
    self.sender = sender  # 檢舉人
    self.time_all = time_all  # 違規日期
    self.undertaker = undertaker  # 承辦人
    self.status = status  # 案件狀態
    self.yy = str(int(time_all[0:4]) - 1911)
    self.mm = time_all[5:7]
    self.dd = time_all[8:10]
    self.hr = time_all[11:13]
    self.min = time_all[14:16]
    self.files = json.dumps(files)  # 將檔案清單轉為json

  def values(self) -> list:
    return [self.number, self.car, self.url, self.place, self.content, self.sender,
            self.yy, self.mm, self.dd, self.hr, self.min, self.files, self.undertaker,self.status]


  def to_dict(self) -> dict:
    case_dict = {
      '案號': self.number,
      '車號': self.car,
      '網址': self.url,
      '地點': self.place,
      '內容': self.content,
      '檢舉人': self.sender,
      '日期': self.time_all,
      '承辦人': self.undertaker,
      '狀態': self.status,
    }
    return case_dict


class CaseReply:
  def __init__(self, ws, row):
    self.number = ws.cell(row, 1).value  # 案號
    self.car = ws.cell(row, 2).value  # 車號
    self.detail_url = ws.cell(row, 3).value  # 案件詳情網址
    self.reply_url = self.detail_url.replace('Details', 'Reply')  # 案件回覆網址
    self.sender = ws.cell(row, 6).value  # 檢舉人
    self.undertaker = ws.cell(row, 13).value[-3:]  # 承辦人姓名（取最後三個字）
    self.status = ws.cell(row, 14).value  # 處理狀態
    self.input: int = ws.cell(row, 16).value  # 輸入簡碼
    self.fine = ws.cell(row, 18).value  # 舉發單號
    self.reject_answer = ws.cell(row, 19).value  # 不舉發理由


  def to_dict(self) -> dict:
    case_dict = {
      '案號': self.number,
      '車號': self.car,
      '網址': self.detail_url,
      '檢舉人': self.sender,
      '承辦人': self.undertaker,
      '狀態': self.status,
      '簡碼': self.input,
      '不舉發理由': self.reject_answer,
    }
    return case_dict
