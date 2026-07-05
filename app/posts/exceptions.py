from app.core.errors import AppError


class PostNotFoundError(AppError):
    def __init__(self, post_id: int) -> None:
        self.post_id = post_id

        super().__init__(
            code="post_not_found",
            message="Post not found",
            status_code=404,
            details={
                "post_id": post_id,
            },
        )
