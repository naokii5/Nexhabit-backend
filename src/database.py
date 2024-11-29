from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv(verbose=True)
user = os.environ.get("SUPABASE_USER")
password = os.environ.get("SUPABASE_PASSWORD")
host = os.environ.get("SUPABASE_HOST")
port = os.environ.get("SUPABASE_PORT")
dbname = os.environ.get("SUPABASE_DBNAME")

DATABASE_URL = f"postgresql+psycopg2://{
    user}:{password}@{host}:{port}/{dbname}"

engine = create_engine(DATABASE_URL, poolclass=NullPool)
Base = declarative_base()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# データベースセッションを取得するための依存関数


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
