from fastapi import FastAPI, Depends
from auth import require_auth
from database import get_connection
from routes import users

app = FastAPI()
app.include_router(users.router)


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