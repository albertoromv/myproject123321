from pydantic import BaseModel, ConfigDict


class UserPostIn(BaseModel):  # data that comes to our API
    body: str


class UserPost(UserPostIn):  # inherites from UserPostIn
    model_config = ConfigDict(
        from_attributes=True
    )  # for SQLAlchemyrow objects (return_value.body)
    id: int  # id of the post
    user_id: int


class CommentIn(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )  # return_value[body] OR return_value.body
    body: str
    post_id: int


class Comment(CommentIn):
    id: int  # id of the comment
    user_id: int


class UserPostWithComments(BaseModel):
    post: UserPost
    comments: list[Comment]
