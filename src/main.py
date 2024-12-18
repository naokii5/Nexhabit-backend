from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import origins
from routers import auth, habits

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


app.include_router(auth.router, tags=["auth"])
app.include_router(habits.router, tags=["habits"])
