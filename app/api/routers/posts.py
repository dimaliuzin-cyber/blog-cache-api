from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Path,
    Response,
    status,
)
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.redis import get_redis
from app.posts import PostService
from app.schemas.posts import (
    PostCreate,
    PostRead,
    PostUpdate,
)


router = APIRouter(prefix="/posts", tags=["posts"])


async def get_post_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    redis_client: Annotated[Redis, Depends(get_redis)]
) -> PostService:
    return PostService(
        session=session,
        redis_client=redis_client,
    )


@router.post(
    "",
    response_model=PostRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать пост",
)
async def create_post(
    post_create: PostCreate,
    service: Annotated[PostService, Depends(get_post_service)],
) -> PostRead:
    post = await service.create_post(post_create)

    return PostRead.model_validate(post)


@router.get(
    "/{post_id}",
    response_model=PostRead,
    status_code=status.HTTP_200_OK,
    summary="Получить пост по id",
)
async def get_post(
    post_id: Annotated[int, Path(gt=0)],
    service: Annotated[PostService, Depends(get_post_service)],
) -> PostRead:
    post = await service.get_post(post_id)

    return PostRead.model_validate(post)


@router.patch(
    "/{post_id}",
    response_model=PostRead,
    status_code=status.HTTP_200_OK,
    summary="Обновить пост по id",
)
async def update_post(
    post_id: Annotated[int, Path(gt=0)],
    post_update: PostUpdate,
    service: Annotated[PostService, Depends(get_post_service)],
) -> PostRead:
    post = await service.update_post(
        post_id=post_id,
        post_update=post_update,
    )

    return PostRead.model_validate(post)


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить пост по id",
)
async def delete_post(
    post_id: Annotated[int, Path(gt=0)],
    service: Annotated[PostService, Depends(get_post_service)],
) -> Response:
    await service.delete_post(post_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)