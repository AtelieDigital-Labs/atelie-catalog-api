from http import HTTPStatus
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import Settings

settings = Settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login/')


class AuthUser:
    def __init__(self, id: str):
        self.id = id


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id: str = payload.get('user_id')

        if not user_id:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail='Token inválido',
            )

        return AuthUser(id=user_id)

    except JWTError:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Token expirado ou inválido',
        )


CurrentUser = Annotated[AuthUser, Depends(get_current_user)]
