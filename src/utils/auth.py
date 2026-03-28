from datetime import datetime
from threading import Lock

from src.utils.log import log

"""
Cookie 管理模組：取代 Selenium，由 pywebview 取得內網認證 Cookie
"""


class CookieStore:
    """管理內網認證 Cookie 的全域單例"""

    def __init__(self) -> None:
        self._cookies: list[dict] | None = None
        self._headers: dict | None = None
        self._last_auth_time: datetime | None = None
        self._lock = Lock()

    def set_cookies(self, cookies: list[dict]) -> None:
        """
        設定從 pywebview 取得的 Cookie
        :param cookies: pywebview 回傳的 Cookie 列表
        """
        with self._lock:
            self._cookies = cookies
            self._last_auth_time = datetime.now()

            # 將 Cookie 轉換為 requests 標頭格式
            cookie_content = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
            self._headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "zh-TW,zh",
                "Connection": "keep-alive",
                "Cookie": cookie_content,
                "Host": "10.124.30.21",
                "Referer": "http://10.124.30.21/",
                "Sec-GPC": "1",
                "Upgrade-Insecure-Requests": "1",
            }
            log().info("Cookie 已更新")
            log().debug(f"Cookie 內容：{cookie_content}")

    def get_headers(self) -> dict | None:
        """取得 requests 可用的 HTTP 標頭（含 Cookie）"""
        with self._lock:
            return self._headers

    def is_authenticated(self) -> bool:
        """檢查是否已取得認證 Cookie"""
        with self._lock:
            return self._headers is not None

    def get_last_auth_time(self) -> str | None:
        """取得最後認證時間的 ISO 格式字串"""
        with self._lock:
            if self._last_auth_time:
                return self._last_auth_time.isoformat()
            return None

    def clear(self) -> None:
        """清除認證狀態"""
        with self._lock:
            self._cookies = None
            self._headers = None
            self._last_auth_time = None
            log().info("Cookie 已清除")


# 全域單例
cookie_store = CookieStore()
