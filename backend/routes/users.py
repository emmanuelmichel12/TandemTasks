from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database import get_connection
from auth import require_auth


router = APIRouter(
    prefix="/users",
    tags=["users"]
)


class UserRegister(BaseModel):
    email: str
    firstname: str


@router.post("/register")
def register_user(
    user: UserRegister,
    auth=Depends(require_auth)
):
    clerk_user_id = auth.payload["sub"]

    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO users (clerk_user_id, email, firstname)
                VALUES (%s, %s, %s)
                RETURNING id, clerk_user_id, email, firstname
                """,
                (clerk_user_id, user.email, user.firstname)
            )

            new_user = cursor.fetchone()

    return {
        "id": new_user[0],
        "clerk_user_id": new_user[1],
        "email": new_user[2],
        "firstname": new_user[3]
    }

#Login user route
@router.get("/me")
def login_user(auth=Depends(require_auth)):
    clerk_user_id = auth.payload["sub"]

    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT id, clerk_user_id, email, firstname
                FROM users
                WHERE clerk_user_id = %s
                """,
                (clerk_user_id,)
            )

            user = cursor.fetchone()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user[0],
        "clerk_user_id": user[1],
        "email": user[2],
        "firstname": user[3]
    }