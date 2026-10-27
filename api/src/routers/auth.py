"""
Authentication Router.
Handles login, token issuance, and current user profile retrieval.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any

from api.src.database import get_db
from api.src.auth import verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    username: str = Field(..., description="System username", example="admin")
    password: str = Field(..., description="Plain-text password", example="AdminSecure2026!")

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    full_name: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

@router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest):
    """Authenticates user credentials and issues a signed JWT token."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, username, email, password_hash, role, full_name, is_active
                FROM curated.users
                WHERE username = %s;
            """, (credentials.username,))
            user = cur.fetchone()

    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated. Please contact an administrator."
        )

    token_data = {
        "sub": user["username"],
        "role": user["role"],
        "user_id": user["id"]
    }
    token = create_access_token(token_data)

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            role=user["role"],
            full_name=user["full_name"] or user["username"]
        )
    )

@router.get("/me", response_model=UserResponse)
def get_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Returns the currently authenticated user's profile."""
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        role=current_user["role"],
        full_name=current_user.get("full_name") or current_user["username"]
    )
