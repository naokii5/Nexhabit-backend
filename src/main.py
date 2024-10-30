from fastapi import FastAPI, HTTPException, Response, Request, Depends, Cookie, BackgroundTasks
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from src.config import origins, supabase
from sqlalchemy.orm import Session
from src.models import Habit, HabitProgress
from src.schemas import HabitCreate, HabitResponse, HabitProgressResponse
from src.database import get_db  # データベース接続セッションを取得するた
from datetime import datetime, date
from litellm import completion
from mangum import Mangum

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


class LoginRequest(BaseModel):
    email: str
    password: str


class User(BaseModel):
    email: str
    password: str


@app.post("/login")
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


@app.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "ログアウトしました。"}


async def get_success_message(habit: HabitResponse, progress: HabitProgressResponse):
    assert habit.id == progress.habit_id
    assert progress.is_checked is True
    habit_name = habit.name
    date = progress.date
    content = f"{habit_name}の進捗が{date}に記録されました。これに対して最大限の賞賛を送ってください。"
    message = completion(model='gemini/gemini-1.5-flash-latest',
                         messages=[{"role": "user", "content": content}])
    return message.choices[0].message.content


async def make_habit_progeress(new_habit: HabitResponse, db: Session):
    progress = db.query(HabitProgress).filter(
        HabitProgress.habit_id == new_habit.id, HabitProgress.date == date.today()).first()
    if progress:
        raise HTTPException(status_code=400, detail="今日は既に進捗が記録されています")
    new_progress = HabitProgress(
        habit_id=new_habit.id, date=date.today())
    new_progress.success_message = get_success_message(new_habit, new_progress)

    db.add(new_progress)
    db.commit()
    db.refresh(new_progress)
    return new_progress


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


@app.get("/profile")
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


@app.post("/habits/create", response_model=HabitResponse)
async def create_habit(habit_data: HabitCreate, request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="ユーザー情報が取得できません")

    # 新しい習慣を作成
    new_habit = Habit(
        name=habit_data.name,
        user_id=user.id,
        start_date=datetime.now().date(),
        is_active=True,
        completed=False,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(new_habit)
    db.commit()
    db.refresh(new_habit)

    background_tasks.add_task(make_habit_progeress, new_habit, db)

    return new_habit


@app.get("/habits/active")
async def get_active_habit(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    habit = db.query(Habit).filter(Habit.user_id == user.id,
                                   Habit.is_active == True).first()
    if not habit:
        raise HTTPException(status_code=404, detail="アクティブな習慣が見つかりません")

    return {"habit": habit}


@app.get("/habits/active/progress")
async def get_habit_progress(db: Session = Depends(get_db), user=Depends(get_current_user)):
    # ユーザーのアクティブな習慣を取得
    habit = db.query(Habit).filter(Habit.user_id == user.id,
                                   Habit.is_active == True).first()
    if not habit:
        print("No active habit")
        raise HTTPException(status_code=404, detail="習慣が見つかりません")

    # 習慣の進捗を取得
    progress = db.query(HabitProgress).filter(
        HabitProgress.habit_id == habit.id).all()
    if not progress:
        print("No progress")
        # raise HTTPException(status_code=404, detail="進捗が見つかりません")
        progress = []
    return {
        "habit": habit,
        "progress": progress
    }


@app.post("/habits/active/progress")
async def check_progress(db: Session = Depends(get_db), user=Depends(get_current_user)):
    # ユーザーのアクティブな習慣を取得
    habit = db.query(Habit).filter(Habit.user_id == user.id,
                                   Habit.is_active == True).first()

    if not habit:
        raise HTTPException(status_code=404, detail="アクティブな習慣が見つかりません")

    # 今日の進捗が既に記録されていないかチェック
    progress = db.query(HabitProgress).filter(
        HabitProgress.habit_id == habit.id, HabitProgress.date == date.today()).first()

    if progress:
        progress.is_checked = True
        db.commit()
        return {"message": "今日の進捗が更新されました", "progress": progress}

    # 新しい進捗を作成
    new_progress = HabitProgress(
        habit_id=habit.id, date=date.today(), is_checked=True)
    new_progress.success_message = get_success_message(habit, new_progress)
    db.add(new_progress)
    db.commit()

    return {"message": "今日の進捗が記録されました", "progress": new_progress}

# @app.post("/habits/active/complete")


class MessageRequest(BaseModel):
    habit: HabitResponse
    progress: HabitProgressResponse


class MessageResponse(BaseModel):
    message: str


handler = Mangum(app)
