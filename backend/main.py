from fastapi import FastAPI, Depends
from database import engine
from sqlalchemy import text
from auth import require_auth

app = FastAPI()


@app.get("/")
def root():
    return {"message": "TandemTask API is running"}


@app.get("/db-test")
def test_database():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return {"database": "connected", "result": result.scalar()}


@app.get("/protected")

def protected_route(auth=Depends(require_auth)):

    return {

        "message": "You are authenticated!",

        "user_id": auth.payload["sub"]

    }