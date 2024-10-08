import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from storeapi.database import comment_table, database, post_table
from storeapi.models.post import (
    Comment,
    CommentIn,
    UserPost,
    UserPostIn,
    UserPostWithComments,
)
from storeapi.models.user import User
from storeapi.security import get_current_user  # , oauth2_scheme

router = APIRouter()

logger = logging.getLogger(__name__)  # storeapi.routers.post


async def find_post(post_id: int):
    logger.info(f"Finding post with id {post_id}")
    query = post_table.select().where(post_table.c.id == post_id)
    logger.debug(query)
    return await database.fetch_one(query)  # fetch_all for all


@router.get("/")  # api.com/
async def root():
    return {"message": "Hello, world!"}


# antes del dependency injection, usaba Request
# Annotated is preferred
@router.post("/post", response_model=UserPost, status_code=201)
async def create_post(
    post: UserPostIn, current_user: Annotated[User, Depends(get_current_user)]
):
    logger.info("Creating post")  # Any quizas por error linter
    # current_user: User = await get_current_user(await oauth2_scheme(request))  # noqa
    # data = post.model_dump()  # as dict
    data = {**post.model_dump(), "user_id": current_user.id}
    query = post_table.insert().values(data)

    logger.debug(query)

    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}


@router.get(
    "/post", response_model=list[UserPost]
)  # the same endpoint can be requested with different petitions, like get or post
async def get_all_posts():
    logger.info("Getting all posts")

    query = post_table.select()

    logger.debug(query)

    return await database.fetch_all(query)


@router.post("/comment", response_model=Comment, status_code=201)
async def create_comment(
    comment: CommentIn, current_user: Annotated[User, Depends(get_current_user)]
):
    logger.info("Creating comment")  # Any quizas por error linter
    # current_user: User = await get_current_user(await oauth2_scheme(request))  # noqa
    post = await find_post(comment.post_id)
    if not post:
        raise HTTPException(
            status_code=404, detail="Post not found"
        )  # 404 is not found
    # data = comment.model_dump()
    data = {**comment.model_dump(), "user_id": current_user.id}
    query = comment_table.insert().values(data)
    last_record_id = await database.execute(query)
    new_comment = {
        **data,
        "id": last_record_id,
    }  # deconstructs the dictionary and creates a new one with one more key

    return new_comment


@router.get("/post/{post_id}/comment", response_model=list[Comment])
async def get_comments_on_post(post_id: int):
    logger.info("Getting comments on post")
    query = comment_table.select().where(comment_table.c.post_id == post_id)
    logger.debug(query)
    return await database.fetch_all(query)


@router.get("/post/{post_id}", response_model=UserPostWithComments)
async def get_post_with_comments(post_id: int):
    logger.info("Getting posts with comments")
    post = await find_post(post_id)
    if not post:
        # logger.error(f"Post with post id {post_id} not found") # not needed if we use the decorator for the exception handler
        raise HTTPException(status_code=404, detail="Post not found")
    return {"post": post, "comments": await get_comments_on_post(post_id)}
