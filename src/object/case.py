import json
import sqlite3
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
    """供匯出 Excel 使用（保留原有格式）"""
    return [self.number, self.car, self.url, self.place, self.content, self.sender,
            self.yy, self.mm, self.dd, self.hr, self.min, json.dumps(self.files), self.undertaker, self.status]

  def to_db_dict(self) -> dict:
    """轉換為 db.insert_case() 所需的字典格式"""
    return {
      'number': self.number,
      'car': self.car,
      'detail_url': self.url,
      'place': self.place,
      'content': self.content,
      'sender': self.sender,
      'year_roc': self.yy,
      'month': self.mm,
      'day': self.dd,
      'hour': self.hr,
      'minute': self.min,
      'files_json': json.dumps(self.files),
      'undertaker': self.undertaker,
      'status': self.status,
    }


class CaseReply(BaseModel):
  """
  從資料庫取得的案件資料，轉化為物件
  用以回覆案件
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
    """從 openpyxl 工作表建立（匯入 Excel 時使用）"""
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

  @classmethod
  def from_db_row(cls, row: sqlite3.Row) -> 'CaseReply':
    """從 SQLite Row 物件建立"""
    return cls(
      number=row['number'],
      car=row['car'],
      detail_url=row['detail_url'],
      content=row['content'],
      sender=row['sender'],
      undertaker=row['undertaker'],
      status=row['status'],
      input=row['input_code'],
      fine=row['fine'],
      reject_answer=row['reject_answer'],
    )
