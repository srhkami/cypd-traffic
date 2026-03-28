import socket
import threading

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
  4. pywebview 開啟內網認證視窗
  5. 認證完成後切換至本地前端頁面
"""

INTRANET_URL = "http://10.124.30.21"


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


def _on_loaded(window: webview.Window, api_port: int) -> None:
    """
    pywebview 視窗載入完成後的回呼
    負責從內網頁面擷取 Cookie，完成認證後切換到本地前端
    """
    import time

    # 等待頁面完全載入
    time.sleep(2)

    current_url = window.get_current_url() or ""
    log().debug(f"目前頁面：{current_url}")

    # 若在內網頁面，嘗試擷取 Cookie
    if "10.124.30.21" in current_url:
        cookies = window.evaluate_js("""
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

        if cookies:
            import json

            cookie_list = json.loads(cookies)
            if cookie_list:
                cookie_store.set_cookies(cookie_list)
                log().info("已從 pywebview 取得內網 Cookie")

        # 切換到本地前端
        window.load_url(f"http://127.0.0.1:{api_port}/")
        log().info("已切換至本地前端頁面")


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
    import time

    time.sleep(1)

    # 3. 建立 pywebview 視窗
    window = webview.create_window(
        title=f"嘉義縣交通違規申訴系統 v{ver}",
        url=INTRANET_URL,
        width=1280,
        height=800,
        resizable=True,
    )

    # 4. 設定認證完成後的回呼
    window.events.loaded += lambda: _on_loaded(window, api_port)

    # 5. 啟動 pywebview（阻塞主執行緒）
    webview.start(debug=True)

    log().debug("GUI 程式結束")


if __name__ == "__main__":
    main()
