from fastapi import APIRouter

from src.api.deps import ok, fail
from src.api.schemas import ArticleOut, ArticleCreate
from src.models.article import get_articles
from src.utils import db

router = APIRouter(prefix="/api/articles", tags=["法條"])


@router.get("")
def list_articles():
    """取得全部法條對照表"""
    articles = get_articles()
    data = [
        ArticleOut(input_key=key, code=art.code, text=art.text).model_dump()
        for key, art in articles.items()
    ]
    return ok(f"取得 {len(data)} 筆法條", data=data)


@router.post("")
def create_or_update_article(body: ArticleCreate):
    """新增或更新法條"""
    db.upsert_article(body.input_key, body.code, body.text)
    return ok(f"已儲存法條：簡碼 {body.input_key}")


@router.delete("/{input_key}")
def remove_article(input_key: int):
    """刪除指定簡碼的法條"""
    count = db.delete_article(input_key)
    if count == 0:
        return fail(f"找不到簡碼 {input_key} 的法條")
    return ok(f"已刪除簡碼 {input_key} 的法條")
