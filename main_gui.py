import json
import socket
import threading
import time

import uvicorn
import webview

from src.utils.log import log
from src.ui.info import ver
from src.utils.db import init_db
from src.utils.auth import cookie_store

"""
GUI 入口：啟動 FastAPI（背景執行緒）+ pywebview（主執行緒）
啟動流程：
  1. init_db() 初始化資料庫
  2. 取得可用連接埠
  3. 在背景執行緒啟動 FastAPI (uvicorn)
  4. pywebview 直接載入本地前端頁面
  5. 使用者需要時手動點擊「登入內網」按鈕觸發認證
"""

INTRANET_URL = "http://10.124.30.21"


class Api:
    """
    暴露給 pywebview 的 JavaScript API
    前端可透過 window.pywebview.api.xxx() 呼叫這些方法
    """

    def __init__(self, main_window: webview.Window) -> None:
        self._main_window = main_window
        self._auth_lock = threading.Lock()

    def login(self) -> dict:
        """
        手動觸發內網認證：開新視窗連到內網頁面取得 Cookie
        認證完成後自動關閉認證視窗
        :return: 認證結果 {success: bool, message: str}
        """
        if not self._auth_lock.acquire(blocking=False):
            return {"success": False, "message": "認證視窗已開啟，請勿重複操作"}

        try:
            return self._do_login()
        finally:
            self._auth_lock.release()

    def _do_login(self) -> dict:
        """執行實際的認證流程"""
        result = {"success": False, "message": "認證失敗"}
        auth_done = threading.Event()

        def _on_auth_loaded(auth_window: webview.Window) -> None:
            """認證視窗載入完成後的回呼，擷取 Cookie"""
            time.sleep(2)

            current_url = auth_window.get_current_url() or ""
            log().debug(f"認證視窗目前頁面：{current_url}")

            if "10.124.30.21" not in current_url:
                log().warning(f"認證視窗未導向內網頁面：{current_url}")
                result["message"] = "未成功連線至內網"
                auth_done.set()
                return

            cookies_json = auth_window.evaluate_js("""
        (function() {
          var cookies = document.cookie.split('; ');
          var result = [];
          for (var i = 0; i < cookies.length; i++) {
            var parts = cookies[i].split('=');
            result.push({name: parts[0], value: parts.slice(1).join('=')});
          }
          return JSON.stringify(result);
        })()
      """)

            if cookies_json:
                cookie_list = json.loads(cookies_json)
                if cookie_list:
                    cookie_store.set_cookies(cookie_list)
                    result["success"] = True
                    result["message"] = "認證成功"
                    log().info("已從認證視窗取得內網 Cookie")

            auth_done.set()

            # 關閉認證視窗
            try:
                auth_window.destroy()
            except Exception:
                pass

        # 在新執行緒中建立認證視窗（pywebview 要求在主執行緒以外使用特定方法）
        auth_window = webview.create_window(
            title="內網認證",
            url=INTRANET_URL,
            width=900,
            height=600,
            resizable=True,
        )

        auth_window.events.loaded += lambda: _on_auth_loaded(auth_window)

        # 等待認證完成（最多 60 秒）
        auth_done.wait(timeout=60)

        if not auth_done.is_set():
            result["message"] = "認證逾時"
            try:
                auth_window.destroy()
            except Exception:
                pass

        return result

    def get_auth_status(self) -> dict:
        """取得目前認證狀態"""
        return {
            "authenticated": cookie_store.is_authenticated(),
            "last_auth_time": cookie_store.get_last_auth_time(),
        }


def _find_free_port() -> int:
    """找到一個可用的連接埠"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _start_api_server(port: int) -> None:
    """在背景執行緒啟動 FastAPI"""
    from src.api.app import create_app

    app = create_app()
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


def main() -> None:
    """GUI 主程式入口"""
    log().debug("！----- GUI 模式開始執行 -----！")
    log().debug(f"程式版本：{ver}")

    # 1. 初始化資料庫
    init_db()

    # 2. 啟動 FastAPI
    api_port = _find_free_port()
    api_thread = threading.Thread(
        target=_start_api_server, args=(api_port,), daemon=True
    )
    api_thread.start()
    log().info(f"FastAPI 已在背景啟動，連接埠：{api_port}")

    # 等待 API 伺服器就緒
    time.sleep(1)

    # 3. 建立 pywebview 視窗，直接載入本地前端
    local_url = f"http://127.0.0.1:{api_port}/"

    window = webview.create_window(
        title=f"嘉義縣交通違規申訴系統 v{ver}",
        url=local_url,
        width=1280,
        height=800,
        resizable=True,
    )

    # 4. 建立 Api 實例並綁定至視窗
    js_api = Api(window)
    window.expose(js_api.login, js_api.get_auth_status)

    # 5. 啟動 pywebview（阻塞主執行緒）
    webview.start(debug=True)

    log().debug("GUI 程式結束")


if __name__ == "__main__":
    main()
