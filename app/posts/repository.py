from sqlalchemy.ext.asyncio import AsyncSession

from app.posts.models import Post
from app.schemas.posts import PostCreate, PostUpdate


class PostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_post(self, post_create: PostCreate) -> Post:
        post = Post(
            title=post_create.title,
            content=post_create.content,
        )

        self._session.add(post)

        await self._session.flush()
        await self._session.refresh(post)

        return post
    
    async def get_post_by_id(self, post_id: int) -> Post | None:
        post = await self._session.get(Post, post_id)

        return post
    
    async def update_post(
        self,
        post_id: int,
        post_update: PostUpdate,
    ) -> Post | None:
        post = await self.get_post_by_id(post_id)

        if post is None:
            return None
        
        update_data = post_update.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        if "title" in update_data:
            post.title = update_data["title"]

        if "content" in update_data:
            post.content = update_data["content"]

        await self._session.flush()
        await self._session.refresh(post)

        return post
    
    async def delete_post(self, post_id: int) -> Post | None:
        post = await self.get_post_by_id(post_id)

        if post is None:
            return None
        
        await self._session.delete(post)
        await self._session.flush()

        return post