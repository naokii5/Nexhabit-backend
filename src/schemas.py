from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class HabitCreate(BaseModel):
    name: str


class HabitResponse(BaseModel):
    id: int
    user_id: UUID
    name: str
    start_date: datetime
    is_active: bool
    completed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HabitProgressResponse(BaseModel):
    id: int
    habit_id: int
    created_at: datetime
    date: datetime
    is_checked: bool
    success_message: str
    failure_message: str

    class Config:
        from_attributes = True
