from fastapi import HTTPException, Cookie
from config import supabase


async def get_current_user(access_token: str | None = Cookie(default=None), refresh_token: str | None = Cookie(default=None)):
    auth_response = supabase.auth.set_session(access_token, refresh_token)
    access_token = auth_response.session.access_token
    if not access_token:
        print("No access token")
        raise HTTPException(status_code=401, detail="認証情報がありません。")

    user_response = supabase.auth.get_user(access_token)

    return user_response.user


async def get_token_from_cookie(access_token: str | None = Cookie(default=None), refresh_token: str | None = Cookie(default=None)):
    auth_response = supabase.auth.set_session(access_token, refresh_token)
    access_token = auth_response.session.access_token
    if (access_token is None):
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return access_token
