import json
from pydantic import BaseModel, computed_field, field_validator


class CaseWeb(BaseModel):
  """
  從網站上取得的案件內容，轉化為物件
  用以轉化為資料庫
  """
  number: str      # 案號
  car: str         # 車號
  url: str         # 案件的網址
  place: str       # 違規地點
  content: str     # 違規內容
  sender: str      # 檢舉人
  time_all: str    # 違規日期（格式：YYYY-MM-DD HH:MM）
  undertaker: str  # 承辦人
  status: str      # 案件狀態
  files: list[str] # 附件連結清單

  @computed_field
  @property
  def yy(self) -> str:
    return str(int(self.time_all[0:4]) - 1911)

  @computed_field
  @property
  def mm(self) -> str:
    return self.time_all[5:7]

  @computed_field
  @property
  def dd(self) -> str:
    return self.time_all[8:10]

  @computed_field
  @property
  def hr(self) -> str:
    return self.time_all[11:13]

  @computed_field
  @property
  def min(self) -> str:
    return self.time_all[14:16]

  def values(self) -> list:
    return [self.number, self.car, self.url, self.place, self.content, self.sender,
            self.yy, self.mm, self.dd, self.hr, self.min, json.dumps(self.files), self.undertaker, self.status]


class CaseReply(BaseModel):
  """
  從Excel中取得的案件資料，轉化為物件
  用以回覆檔案
  """
  number: str           # 案號
  car: str              # 車號
  detail_url: str       # 案件詳情網址
  content: str          # 案件內容
  sender: str           # 檢舉人
  undertaker: str       # 承辦人姓名（取最後三個字）
  status: str           # 處理狀態
  input: int            # 輸入簡碼
  fine: str | None = None           # 舉發單號
  reject_answer: str | None = None  # 不舉發理由

  @computed_field
  @property
  def reply_url(self) -> str:
    return self.detail_url.replace('Details', 'Reply')

  @field_validator('undertaker', mode='before')
  @classmethod
  def take_last_three(cls, v):
    if isinstance(v, str):
      return v[-3:]
    return v

  @classmethod
  def from_worksheet(cls, ws, row: int) -> 'CaseReply':
    return cls(
      number=ws.cell(row, 1).value,
      car=ws.cell(row, 2).value,
      detail_url=ws.cell(row, 3).value,
      content=ws.cell(row, 5).value,
      sender=ws.cell(row, 6).value,
      undertaker=ws.cell(row, 13).value,
      status=ws.cell(row, 14).value,
      input=ws.cell(row, 16).value,
      fine=ws.cell(row, 18).value,
      reject_answer=ws.cell(row, 19).value,
    )
