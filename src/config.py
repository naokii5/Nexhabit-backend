import os
from supabase import create_client, Client
from supabase.client import ClientOptions
import google.generativeai as genai

from dotenv import load_dotenv
load_dotenv(verbose=True)

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
frontend_url: str = os.environ.get("FRONTEND_URL")
supabase: Client = create_client(url, key,
                                 options=ClientOptions(
                                     postgrest_client_timeout=10,
                                     storage_client_timeout=10,
                                     schema="public",
                                 ))

# CORSの設定（フロントエンドからのリクエストを許可）
origins = [
    "http://localhost:5174",  # フロントエンドのURL
    "http://127.0.0.1:5174",  # 必要なら他のオリジンも追加
]


GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
gemini = genai.GenerativeModel("gemini-1.5-flash")
