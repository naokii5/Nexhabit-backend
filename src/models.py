import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Index, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base  # 既存のBaseクラス


class Habit(Base):
    __tablename__ = 'habits'

    id = Column(Integer, primary_key=True, index=True)
    # Supabase の auth.users テーブルの id を参照
    user_id = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)
    name = Column(String, nullable=False)
    start_date = Column(Date, default=datetime.now().date)
    is_active = Column(Boolean, default=True)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # ユーザーごとにアクティブな習慣が1つしか存在できない制約
    __table_args__ = (
        Index('unique_active_habit_per_user', 'user_id',
              unique=True, postgresql_where=(is_active is True)),
    )

    # HabitProgressとのリレーションシップ
    progress = relationship("HabitProgress", back_populates="habit")


class HabitProgress(Base):
    __tablename__ = 'habit_progress'
    id = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey('habits.id'))
    created_at = Column(DateTime, default=datetime.now)
    date = Column(Date, default=datetime.now().date)
    is_checked = Column(Boolean, default=False)
    success_message = Column(String, nullable=True)
    failure_message = Column(String, nullable=True)

    # Habit テーブルとのリレーションシップ
    habit = relationship("Habit", back_populates="progress")
