from http import HTTPStatus
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import Settings
from app.core.context import current_user_id

settings = Settings()

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login/', auto_error=True)
async def get_token_from_cookie_or_header(request: Request) -> str | None:
    # 1. Tenta buscar nos cookies do navegador
    token = request.cookies.get("access_token") # Altere para o nome real do seu cookie
    
    if token:
        return token

    # 2. Se não achou no cookie, tenta buscar no cabeçalho Authorization
    authorization: str = request.headers.get("Authorization")
    if authorization:
        try:
            scheme, param = authorization.split()
            if scheme.lower() == "bearer":
                return param
        except ValueError:
            return None

    return None

class AuthUser:
    def __init__(self, id: str):
        self.id = id


# async def get_current_user(
#     token: Annotated[str, Depends(oauth2_scheme)],
# ):
#     try:
#         payload = jwt.decode(
#             token,
#             settings.SECRET_KEY,
#             algorithms=[settings.ALGORITHM],
#         )
#         user_id: str = payload.get('user_id')

#         current_user_id.set(user_id)

#         if not user_id:
#             raise HTTPException(
#                 status_code=HTTPStatus.UNAUTHORIZED,
#                 detail='Token inválido',
#             )

#         return AuthUser(id=user_id)

#     except JWTError:
#         raise HTTPException(
#             status_code=HTTPStatus.UNAUTHORIZED,
#             detail='Token expirado ou inválido',
#         )

async def get_current_user_none(
    token: Annotated[str | None, Depends(get_token_from_cookie_or_header)],
) -> AuthUser | None:
    if token is None:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        user_id = payload.get("user_id")

        if not user_id:
            return None

        current_user_id.set(user_id)

        return AuthUser(id=user_id)

    except JWTError:
        return None

CurrentUserOrNone = Annotated[AuthUser | None, Depends(get_current_user_none)]

async def get_current_user(
    user: CurrentUserOrNone,
) -> AuthUser:
    if user is None:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Token inválido ou ausente",
        )

    return user

CurrentUser = Annotated[AuthUser, Depends(get_current_user)]
