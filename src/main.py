from fastapi import FastAPI, HTTPException, Response, Request, Depends, Cookie
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from src.config import origins, supabase
app = FastAPI()


@app.get("/ping")
async def ping():
    return {"message": "pong"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# サインアップのリクエストボディ


class SignUpRequest(BaseModel):
    email: str
    password: str


@app.post("/signup")
def sign_up(sign_up_request: SignUpRequest):
    try:
        auth_response = supabase.auth.sign_up({
            "email": sign_up_request.email,
            "password": sign_up_request.password
        })
    except Exception as e:
        print(auth_response)
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "Sign-up successful. Please check your email for verification."}


class LoginRequest(BaseModel):
    email: str
    password: str


class User(BaseModel):
    email: str
    password: str


@app.post("/login")
def login(user: User, response: Response):
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": user.email,
            "password": user.password
        })
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))

    access_token = auth_response.session.access_token

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite=None
    )
    print(response.headers)

    return {"message": "ログインに成功しました。"}


@app.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "ログアウトしました。"}


def get_current_user(request: Request):
    access_token = request.cookies.get("access_token")
    print(f"Cookies: {request.cookies}")
    print(f"access_token: {access_token}")

    if not access_token:
        print("No access token")
        raise HTTPException(status_code=401, detail="認証情報がありません。")

    # JWT トークンを明示的に渡してユーザー情報を取得
    user_response = supabase.auth.get_user(access_token)
    if user_response.error:
        print(user_response.error)
        raise HTTPException(status_code=401, detail="無効なトークンです。")

    return user_response.user


def get_token_from_cookie(access_token: str | None = Cookie(default=None)):
    if (access_token is None):
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return access_token


@app.get("/profile")
def read_profile(jwt=Depends(get_token_from_cookie)):
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
