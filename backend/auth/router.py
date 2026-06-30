from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from backend.database.connection import get_connection
from backend.auth.models import UserRegister, UserResponse, TokenResponse
from backend.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
)
from backend.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse)
def register(body: UserRegister):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s", (body.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="用户名已存在")

        cursor.execute(
            "INSERT INTO users (username, email, hashed_password) VALUES (%s, %s, %s)",
            (body.username, body.email, hash_password(body.password)),
        )
        user_id = cursor.lastrowid

        cursor.execute(
            "SELECT id, username, email, is_active FROM users WHERE id = %s",
            (user_id,),
        )
        return cursor.fetchone()


@router.post("/login/access-token", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, hashed_password, is_active FROM users WHERE username = %s",
            (form_data.username,),
        )
        row = cursor.fetchone()

    if not row or not verify_password(form_data.password, row["hashed_password"]):
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    if not row["is_active"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已被禁用")

    token = create_access_token(row["id"])
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_me(user: UserResponse = Depends(get_current_user)):
    return user
