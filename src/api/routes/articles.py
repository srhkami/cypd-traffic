from fastapi import APIRouter

from src.api.deps import ok
from src.api.schemas import ArticleOut
from src.models.article import get_articles

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
