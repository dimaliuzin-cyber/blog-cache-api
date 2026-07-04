class PostNotFoundError(Exception):
    def __init__(self, post_id: int) -> None:
        self.post_id = post_id
        super().__init__(f"Post with id={post_id} was not found")