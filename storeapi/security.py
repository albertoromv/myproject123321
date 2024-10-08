import datetime
import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from storeapi.config import config
from storeapi.database import database, user_table

logger = logging.getLogger(__name__)  # storeapi.security

JWT_SECRET_KEY = config.JWT_SECRET_KEY
JWT_ALGORITHM = config.JWT_ALGORITHM
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token"
)  # in user router, the token endpoint, where the client sends the email and password and gets back the token

pwd_context = CryptContext(schemes=["bcrypt"])

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def access_token_expire_minutes() -> int:  # to mock the expiracy of the token
    return 30


def create_access_token(email: str):  # because emails are unique, so the ID
    logger.debug("creating access token", extra={"email": email})

    expire = int(
        (
            datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(minutes=access_token_expire_minutes())
        ).timestamp()
    )  # important in Madrid!

    logger.debug(expire)
    logger.debug(datetime.datetime.now(datetime.timezone.utc))
    logger.debug(datetime.timedelta(minutes=access_token_expire_minutes()))

    jwt_data = {"sub": email, "exp": expire}
    encoded_jwt = jwt.encode(jwt_data, key=JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(
        plain_password, hashed_password
    )  # unique seeds, the same password hashed twice doesn't create the same hash values
    # verify uses info from the hashed password to hash in the same way the plain password


async def get_user(email: str):
    logger.debug("Fetching user from the database", extra={"email": email})
    query = user_table.select().where(user_table.c.email == email)
    result = await database.fetch_one(query)
    if result:
        return result


async def authenticate_user(email: str, password: str):
    logger.debug("Authenticating user", extra={"email": email})
    user = await get_user(email)
    if not user:  # user doesn't exist
        # pass
        raise credentials_exception
    if not verify_password(
        password, user.password
    ):  # the plain password doesn't match the hashed password
        # pass
        raise credentials_exception
    return user


# token is a str, take it from oauth2_scheme
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, key=JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception

    except ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    except JWTError as e:
        raise credentials_exception from e

    user = await get_user(email=email)
    if user is None:
        raise credentials_exception
    return user
