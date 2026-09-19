from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import secrets
import string

from database import get_connection
from auth import require_auth

router = APIRouter(
    prefix="/workspaces",
    tags=["workspaces"]
)

class WorkspaceCreate(BaseModel):
    space_name: str

def generate_code():
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(8))


@router.post("/create")
def create_workspace(workspace: WorkspaceCreate, auth=Depends(require_auth)):
    clerk_user_id = auth.payload["sub"]

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE clerk_user_id = %s
                """,
                (clerk_user_id,)
            )
            user = cursor.fetchone()

            if user is None:
                raise HTTPException(status_code=404, detail="User not found")

            owner_id = user[0]

            cursor.execute(
                """
                INSERT INTO workspaces (owner_id, space_name, join_code)
                VALUES (%s, %s, %s)
                RETURNING id, owner_id, space_name, join_code
                """,
                (owner_id, workspace.space_name, generate_code())
            )

            new_workspace = cursor.fetchone()

    return {
        "id": new_workspace[0],
        "owner_id": new_workspace[1],
        "space_name": new_workspace[2],
        "join_code": new_workspace[3]
    }