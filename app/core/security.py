from http import HTTPStatus
from typing import Annotated
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError # Agora usando jose que você instalou
from app.core.config import Settings

settings = Settings()

# 1. Onde o Swagger vai buscar o token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/token-mock')

# 2. Modelo simples para representar o usuário logado
class AuthUser:
    def __init__(self, artisan_id: str):
        self.id = artisan_id

# 3. A função que PROTEGE as suas rotas
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    # Atalho para testes manuais rápidos
    if token == 'fake-token':
        return AuthUser(artisan_id='artisan-123-fake')

    try:
        # Decodifica o token gerado pelo auth_test.py
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        artisan_id: str = payload.get('sub')

        if not artisan_id:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED, 
                detail='Token inválido: sub ausente'
            )

        return AuthUser(artisan_id=artisan_id)

    except (JWTError, Exception): # Captura erro de assinatura ou expiração
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Token expirado ou inválido',
        )

# 4. Um "tipo" para facilitar o uso nas rotas
CurrentUser = Annotated[AuthUser, Depends(get_current_user)]