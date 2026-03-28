import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.api.routes import (
    cases,
    articles,
    undertakers,
    options,
    auth,
    scrape,
    reply,
    download,
    excel,
    tasks,
)


def create_app() -> FastAPI:
    """
    建立 FastAPI 應用程式
    掛載所有路由與靜態檔案
    """
    app = FastAPI(
        title="嘉義縣交通違規申訴系統 API",
        description="提供案件管理、爬取、回覆、下載等功能的 RESTful API",
        version="1.0.0",
    )

    # ── 掛載 API 路由 ──
    app.include_router(cases.router)
    app.include_router(articles.router)
    app.include_router(undertakers.router)
    app.include_router(options.router)
    app.include_router(auth.router)
    app.include_router(scrape.router)
    app.include_router(reply.router)
    app.include_router(download.router)
    app.include_router(excel.router)
    app.include_router(tasks.router)

    # ── 掛載靜態前端檔案 ──
    web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web")
    if os.path.exists(web_dir):
        app.mount("/", StaticFiles(directory=web_dir, html=True), name="web")

    return app
