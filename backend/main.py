from fastapi import FastAPI, Depends
from auth import require_auth
from database import get_connection
from routes import users, workspaces, tasks, ws
from contextlib import asynccontextmanager
import asyncio
from redis_client import redis_listener

@asynccontextmanager
async def lifespan(app: FastAPI):
    listener_task = asyncio.create_task(redis_listener())
    yield
    listener_task.cancel()

app = FastAPI(lifespan=lifespan)
app.include_router(users.router)
app.include_router(workspaces.router)
app.include_router(tasks.router)
app.include_router(ws.router)
    


@app.get("/")
def root():
    return {"message": "TandemTask API is running"}


@app.get("/db-test")
def test_database():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

    return {
        "database": "connected",
        "result": result[0]
    }

@app.get("/protected")

def protected_route(auth=Depends(require_auth)):

    return {

        "message": "You are authenticated!",

        "user_id": auth.payload["sub"]

    }