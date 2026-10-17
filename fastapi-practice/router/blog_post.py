from typing import Optional, List, Dict

from fastapi import APIRouter, Query, Body, Path
from pydantic import BaseModel

router = APIRouter(
    prefix='/blog',
    tags=['blog'],
)


class Image(BaseModel):
    url: str
    alias: str


class BlogModel(BaseModel):
    title: str
    content: str
    published: Optional[bool] = False
    tags: List[str] = []
    metadata: Dict[str, str] = {'key1': 'value1', 'key2': 'value2'}
    image: Optional[Image] = None


@router.post('/new/{id}')
def create_blog(blog: BlogModel, id: int, version: int = 1):
    return {
        'id': id,
        'data': blog,
        'version': version
    }


@router.post('/new/{id}/comment/{comment_id}')
def create_comment(
        blog: BlogModel,
        id: int,
        comment_title: str = Query(
            None,
            title='Comment title',
            description='some description for comment title',
            alias='commentTitle',
            deprecated=True,
        ),
        content: str = Body(
            ...,
            min_length=10,
            max_length=12,
            pattern=r'^[a-z]*$',
        ),
        v: Optional[List[str]] = Query(['1.1', '1.2', '1.3']),
        comment_id: int = Path(gt=5, le=10),
):
    return {
        'blog': blog,
        'id': id,
        'comment_id': comment_id,
        'content': content,
        'version': v,
        'comment_title': comment_title,
    }


def required_functionality():
    return {"message", "Learning FastAPI is important"}
