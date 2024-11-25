from fastapi import APIRouter, HTTPException, Response, Depends
from config import supabase
from schemas import SignUpRequest, User
from routers.dependencies import get_token_from_cookie
router = APIRouter()


@router.post("/signup")
async def sign_up(sign_up_request: SignUpRequest):
    try:
        auth_response = supabase.auth.sign_up({
            "email": sign_up_request.email,
            "password": sign_up_request.password
        })
    except Exception as e:
        print(auth_response)
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "Sign-up successful. Please check your email for verification."}


@router.post("/login")
async def login(user: User, response: Response):
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": user.email,
            "password": user.password
        })
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))

    access_token = auth_response.session.access_token
    refresh_token = auth_response.session.refresh_token
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite=None
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite=None
    )
    print(response.headers)

    return {"message": "ログインに成功しました。"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "ログアウトしました。"}


@router.get("/profile")
async def read_profile(jwt=Depends(get_token_from_cookie)):
    try:
        user_response = supabase.auth.get_user(jwt)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))
    current_user = user_response.user

    return {
        "email": current_user.email,
        "user_metadata": current_user.user_metadata,
    }
