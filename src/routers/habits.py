from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from models import Habit, HabitProgress
from schemas import HabitCreate, HabitResponse
from database import get_db
from datetime import datetime, date
from routers.dependencies import get_current_user, make_habit_progress

router = APIRouter()


@router.post("/habits/create", response_model=HabitResponse)
async def create_habit(habit_data: HabitCreate, request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user=Depends(get_current_user)):
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

    background_tasks.add_task(make_habit_progress, new_habit, db)

    return new_habit


@router.get("/habits/active")
async def get_active_habit(db: Session = Depends(get_db), user=Depends(get_current_user)):
    habit = db.query(Habit).filter(Habit.user_id == user.id,
                                   Habit.is_active == True).first()
    if not habit:
        raise HTTPException(status_code=404, detail="アクティブな習慣が見つかりません")

    return {"habit": habit}


@router.get("/habits/active/progress")
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


@router.post("/habits/active/progress")
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
    new_progress = make_habit_progress(habit, db)
    db.add(new_progress)
    db.commit()

    return {"message": "今日の進捗が記録されました", "progress": new_progress}
