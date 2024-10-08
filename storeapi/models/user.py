from pydantic import BaseModel


class User(BaseModel):
    id: int | None = None
    email: str


class UserIn(User):  # so that we don't retrieve the password
    password: str
