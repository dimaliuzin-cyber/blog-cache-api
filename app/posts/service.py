from sqlalchemy.ext.asyncio import AsyncSession

from app.posts.exceptions import PostNotFoundError
from app.posts.models import Post
from app.posts.repository import PostRepository
from app.schemas.posts import PostCreate, PostUpdate


class PostService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = PostRepository(session)

    async def create_post(self, post_create: PostCreate) -> Post:
        post = await self._repository.create_post(post_create)

        await self._commit_transaction()
        await self._session.refresh(post)

        return post
    
    async def get_post(self, post_id: int) -> Post:
        post = await self._repository.get_post_by_id(post_id)

        if post is None:
            raise PostNotFoundError(post_id)
        
        return post
    
    async def update_post(
        self,
        post_id: int,
        post_update: PostUpdate,
    ) -> Post:
        post = await self._repository.update_post(
            post_id=post_id,
            post_update=post_update,
        )

        if post is None:
            raise PostNotFoundError(post_id)
        
        await self._commit_transaction()
        await self._session.refresh(post)
        
        return post
    
    async def delete_post(self, post_id: int) -> Post:
        post = await self._repository.delete_post(post_id)

        if post is None:
            raise PostNotFoundError(post_id)
        
        await self._commit_transaction()

        return post
    
    async def _commit_transaction(self) -> None:
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise