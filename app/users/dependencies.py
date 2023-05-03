from fastapi import Request, HTTPException, Depends, status
from jose import jwt, JWTError

from app.config import settings


def get_token(request: Request):
    token = request.cookies.get('booking_access_token')
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return token


def get_current_user(token: str = Depends(get_token)):
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, settings.ALGORITHM
        )
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    expire: str = payload.get('exp')
