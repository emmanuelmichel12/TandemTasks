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


class WorkspaceJoin(BaseModel):
    join_code: str


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

            # The owner is automatically a member of their own workspace,
            # otherwise they'd be locked out of the task endpoints below,
            # which all gate access through workspace_members.
            cursor.execute(
                """
                INSERT INTO workspace_members (workspace_id, user_id)
                VALUES (%s, %s)
                ON CONFLICT (workspace_id, user_id) DO NOTHING
                """,
                (new_workspace[0], owner_id)
            )

    return {
        "id": new_workspace[0],
        "owner_id": new_workspace[1],
        "space_name": new_workspace[2],
        "join_code": new_workspace[3]
    }


@router.post("/join")
def join_workspace(payload: WorkspaceJoin, auth=Depends(require_auth)):
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

            user_id = user[0]

            cursor.execute(
                """
                SELECT id, space_name
                FROM workspaces
                WHERE join_code = %s
                """,
                (payload.join_code,)
            )
            workspace = cursor.fetchone()

            if workspace is None:
                raise HTTPException(status_code=404, detail="Invalid join code")

            workspace_id, space_name = workspace

            cursor.execute(
                """
                INSERT INTO workspace_members (workspace_id, user_id)
                VALUES (%s, %s)
                ON CONFLICT (workspace_id, user_id) DO NOTHING
                RETURNING id
                """,
                (workspace_id, user_id)
            )
            inserted = cursor.fetchone()

    return {
        "workspace_id": workspace_id,
        "space_name": space_name,
        "already_member": inserted is None
    }

@router.get("/list")
def list_workspaces(auth=Depends(require_auth)):
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

            user_id = user[0]

            cursor.execute(
                """
                SELECT w.id, w.space_name, w.join_code
                FROM workspaces w
                JOIN workspace_members wm ON w.id = wm.workspace_id
                WHERE wm.user_id = %s
                """,
                (user_id,)
            )
            workspaces = cursor.fetchall()

    return [
        {
            "id": workspace[0],
            "space_name": workspace[1],
            "join_code": workspace[2]
        }
        for workspace in workspaces
    ]

@router.get("/{workspace_id}/members")
def list_workspace_members(workspace_id: int, auth=Depends(require_auth)):
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

            user_id = user[0]

            # Check if the user is a member of the workspace
            cursor.execute(
                """
                SELECT 1
                FROM workspace_members
                WHERE workspace_id = %s AND user_id = %s
                """,
                (workspace_id, user_id)
            )
            is_member = cursor.fetchone()

            if is_member is None:
                raise HTTPException(status_code=403, detail="Not a member of this workspace")

            # Fetch members of the workspace
            cursor.execute(
                """
                SELECT u.id, u.email, u.firstname
                FROM users u
                JOIN workspace_members wm ON u.id = wm.user_id
                WHERE wm.workspace_id = %s
                """,
                (workspace_id,)
            )
            members = cursor.fetchall()

    return [
        {
            "id": member[0],
            "email": member[1],
            "firstname": member[2]
        }
        for member in members
    ]