from typing import Annotated

from fastapi import APIRouter, Body, Cookie, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db import get_session
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

_COOKIE_NAME = "refresh_token"
_COOKIE_MAX_AGE = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=_COOKIE_MAX_AGE,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=_COOKIE_NAME, httponly=True, samesite="lax")


@router.post("/register", response_model=LoginResponse, status_code=201)
async def register(
    data: RegisterRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> LoginResponse:
    service = AuthService(session)
    result, raw_token = await service.register(data)
    _set_refresh_cookie(response, raw_token)
    return result


@router.post("/login", response_model=LoginResponse)
async def login(
    data: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> LoginResponse:
    service = AuthService(session)
    login_response, raw_token = await service.login(data)
    _set_refresh_cookie(response, raw_token)
    return login_response


@router.post("/refresh", response_model=LoginResponse)
async def refresh(
    response: Response,
    cookie_token: Annotated[str | None, Cookie(alias=_COOKIE_NAME)] = None,
    body: Annotated[RefreshRequest | None, Body()] = None,
    session: AsyncSession = Depends(get_session),
) -> LoginResponse:
    token = cookie_token or (body.refresh_token if body else None)
    if not token:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
        )
    service = AuthService(session)
    login_response, raw_token = await service.refresh(token)
    _set_refresh_cookie(response, raw_token)
    return login_response


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    cookie_token: Annotated[str | None, Cookie(alias=_COOKIE_NAME)] = None,
    body: Annotated[LogoutRequest | None, Body()] = None,
    session: AsyncSession = Depends(get_session),
) -> None:
    token = cookie_token or (body.refresh_token if body else None)
    if token:
        service = AuthService(session)
        await service.logout(token)
    _clear_refresh_cookie(response)
