import os
from supabase import create_client, Client
from supabase.client import ClientOptions
from dotenv import load_dotenv
load_dotenv(verbose=True)

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(url, key,
                                 options=ClientOptions(
                                     postgrest_client_timeout=10,
                                     storage_client_timeout=10,
                                     schema="public",
                                 ))

# CORSの設定（フロントエンドからのリクエストを許可）
origins = [
    "http://localhost:5173",  # フロントエンドのアドレス
    "http://127.0.0.1:5173",
]
