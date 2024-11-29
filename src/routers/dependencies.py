from fastapi import HTTPException, Cookie
from config import supabase, gemini
from datetime import datetime
from models import HabitProgress
from sqlalchemy.orm import Session


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


async def generate_messages_with_gemini(habit_name, date):
    # 日本語でのプロンプトを作成
    success_prompt = f"私は{date}に「{
        habit_name}」という習慣を無事に達成しました。これを褒めるメッセージを日本語で作成してください。"
    failure_prompt = f"私は{date}に「{
        habit_name}」という習慣を達成できませんでした。これからも続けられるように励ますメッセージを日本語で作成してください。"

    # Gemini APIを使ってメッセージを生成
    success_message = await gemini.generate_message(success_prompt)
    failure_message = await gemini.generate_message(failure_prompt)

    return success_message, failure_message


async def make_habit_progress(habit, db: Session):
    # 今日の日付を取得
    today = datetime.now().date()

    # 既に今日の進捗が存在しないか確認
    existing_progress = db.query(HabitProgress).filter(
        HabitProgress.habit_id == habit.id,
        HabitProgress.date == today
    ).first()

    if not existing_progress:
        # Geminiとやり取りしてメッセージを生成
        success_message, failure_message = generate_messages_with_gemini(
            habit.name, today)

        # 今日の進捗データを作成
        new_progress = HabitProgress(
            habit_id=habit.id,
            date=today,
            is_checked=False,  # 初期状態は未チェック
            success_message=success_message,
            failure_message=failure_message
        )
        db.add(new_progress)
        db.commit()
