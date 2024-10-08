from fastapi import APIRouter, HTTPException

from storeapi.models.post import (
    Comment,
    CommentIn,
    UserPost,
    UserPostIn,
    UserPostWithComments,
)

router = APIRouter()

post_table: dict = {}  # everytime we save this file, this is overriden and the dictionary is emptied. We'll use databases later
comment_table: dict = {}


def find_post(post_id: int):
    return post_table.get(post_id)


@router.get("/")  # api.com/
async def root():
    return {"message": "Hello, world!"}


@router.post("/post", response_model=UserPost, status_code=201)
async def create_post(post: UserPostIn):
    data = post.model_dump()
    last_record_id = len(post_table)
    new_post = {
        **data,
        "id": last_record_id,
    }  # deconstructs the dictionary and creates a new one with one more key
    post_table[last_record_id] = new_post
    return new_post


@router.get(
    "/post", response_model=list[UserPost]
)  # the same endpoint can be requested with different petitions, like get or post
async def get_all_posts():
    return list(post_table.values())


@router.post("/comment", response_model=Comment, status_code=201)
async def create_comment(comment: CommentIn):
    post = find_post(comment.post_id)
    if not post:
        raise HTTPException(
            status_code=404, detail="Post not found"
        )  # 404 is not found
    data = comment.model_dump()
    last_record_id = len(comment_table)
    new_comment = {
        **data,
        "id": last_record_id,
    }  # deconstructs the dictionary and creates a new one with one more key
    comment_table[last_record_id] = new_comment
    return new_comment


@router.get("/post/{post_id}/comment", response_model=list[Comment])
async def get_comments_on_post(post_id: int):
    return [
        comment for comment in comment_table.values() if comment["post_id"] == post_id
    ]


@router.get("/post/{post_id}", response_model=UserPostWithComments)
async def get_post_with_comments(post_id: int):
    post = find_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"post": post, "comments": await get_comments_on_post(post_id)}
