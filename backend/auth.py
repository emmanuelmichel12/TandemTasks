import os

from dotenv import load_dotenv
from fastapi import HTTPException, Request
from clerk_backend_api import AuthenticateRequestOptions, authenticate_request

load_dotenv()

class TokenHeader:
    def __init__(self, token: str):
        self.headers = {"Authorization": f"Bearer {token}"}

def require_auth_ws(token: str | None):
    if token is None:
        return None

    state = authenticate_request(
        TokenHeader(token),
        AuthenticateRequestOptions(
            secret_key=os.getenv("CLERK_SECRET_KEY"),
            accepts_token=["session_token"],
        ),
    )

    return state if state.is_authenticated else None

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