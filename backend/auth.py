import os

from dotenv import load_dotenv
from fastapi import HTTPException, Request
from clerk_backend_api import AuthenticateRequestOptions, authenticate_request

load_dotenv()


def require_auth(request: Request):
    state = authenticate_request(
        request,
        AuthenticateRequestOptions(
            secret_key=os.getenv("CLERK_SECRET_KEY"),
            accepts_token=["session_token"],
        ),
    )

    if not state.is_authenticated:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    return state