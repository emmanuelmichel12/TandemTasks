from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database import get_connection
from auth import require_auth

router = APIRouter(
    prefix = "/tasks",
    tags = ["tasks"]
)

class TaskCreate(BaseModel):
    title: str
    task_description: str | None = None
    workspace_id: int
    assigned_to: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    task_description: str | None = None
    assigned_to: int | None = None
    task_status: str | None = None

@router.post("/create")
def create_task(task: TaskCreate, auth = Depends(require_auth)):
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

            created_by = user[0]

            cursor.execute(
                """
                INSERT INTO tasks ( title, task_description, workspace_id, assigned_to, created_by)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, title, task_description, workspace_id, assigned_to, tasked_status, created_by
                """,
                (task.title, task.task_description, task.workspace_id,
                 task.assigned_to, created_by)
            )

            new_task = cursor.fetchone()

    return {
        "id": new_task[0],
        "title": new_task[1],
        "task_description": new_task[2],
        "workspace_id": new_task[3],
        "assigned_to": new_task[4],
        "task_status": new_task[5],
        "created_by": new_task[6]
    }


@router.get("/workspace/{workspace_id}")
def get_tasks(workspace_id: int, auth = Depends(require_auth)):
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
                SELECT id
                FROM workspace_members
                WHERE workspace_id = %s AND user_id = %s
                """,
                (workspace_id, user_id)
            )

            member = cursor.fetchone()

            if member is None:
                raise HTTPException(status_code=403, detail="User is not a member of this workspace")
            cursor.execute(
                """
                SELECT id, title, task_description, workspace_id, assigned_to, task_status, created_by
                FROM tasks
                WHERE workspace_id = %s
                """,
                (workspace_id,)
            )

            tasks = cursor.fetchall()

    return [
        {
            "id": task[0],
            "title": task[1],
            "task_description": task[2],
            "workspace_id": task[3],
            "assigned_to": task[4],
            "task_status": task[5],
            "created_by": task[6]
        }
        for task in tasks
    ]


@router.patch("/update/{task_id}")
def update_task(task_id: int, task: TaskUpdate, auth = Depends(require_auth)):
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
                SELECT workspace_id
                FROM tasks
                WHERE id = %s
                """,
                (task_id,)
            )

            existing_task = cursor.fetchone()
            if existing_task is None:
                raise HTTPException(status_code=404, detail="Task not found")

            workspace_id = existing_task[0]

            cursor.execute(
                """
                SELECT id
                FROM workspace_members
                WHERE workspace_id = %s AND user_id = %s
                """,
                (workspace_id, user_id)
            )
            member = cursor.fetchone()

            if member is None:
                raise HTTPException(status_code=403, detail="User is not authorized to update this task")
            cursor.execute(
                """
                UPDATE tasks
                SET title = COALESCE(%s, title), task_description = COALESCE(%s, task_description), assigned_to = COALESCE(%s, assigned_to), task_status = COALESCE(%s, task_status)
                WHERE id = %s
                RETURNING id, title, task_description, workspace_id, assigned_to, task_status, created_by
                """,
                (task.title, task.task_description,
                 task.assigned_to, task.task_status, task_id)
            )

            updated_task = cursor.fetchone()

    if not updated_task:
        raise HTTPException(status_code=404, detail="Task not found or not authorized to update")

    return {
        "id": updated_task[0],
        "title": updated_task[1],
        "task_description": updated_task[2],
        "workspace_id": updated_task[3],
        "assigned_to": updated_task[4],
        "task_status": updated_task[5],
        "created_by": updated_task[6]
    }


@router.delete("/delete/{task_id}")
def delete_task(task_id: int, auth=Depends(require_auth)):
    clerk_user_id = auth.payload["sub"]

    with get_connection() as connection:
        with connection.cursor() as cursor:

            # Find logged-in user
            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE clerk_user_id = %s
                """,
                (clerk_user_id,)
            )

            user = cursor.fetchone()

            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="User not found"
                )

            user_id = user[0]

            # Find task and its workspace
            cursor.execute(
                """
                SELECT workspace_id
                FROM tasks
                WHERE id = %s
                """,
                (task_id,)
            )

            existing_task = cursor.fetchone()

            if not existing_task:
                raise HTTPException(
                    status_code=404,
                    detail="Task not found"
                )

            workspace_id = existing_task[0]

            # Check that user belongs to the workspace
            cursor.execute(
                """
                SELECT id
                FROM workspace_members
                WHERE workspace_id = %s AND user_id = %s
                """,
                (workspace_id, user_id)
            )

            member = cursor.fetchone()

            if not member:
                raise HTTPException(
                    status_code=403,
                    detail="User is not a member of this workspace"
                )

            # Delete only if this user created the task
            cursor.execute(
                """
                DELETE FROM tasks
                WHERE id = %s AND created_by = %s
                RETURNING id
                """,
                (task_id, user_id)
            )

            deleted_task = cursor.fetchone()

            if not deleted_task:
                raise HTTPException(
                    status_code=403,
                    detail="Only the task creator can delete this task"
                )

    return {
        "message": "Task deleted successfully",
        "task_id": deleted_task[0]
    }