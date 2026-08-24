"""
认证相关 API 路由。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, UserResponse, TokenResponse
from app.services.auth_service import (
    register_user,
    authenticate_user,
    create_access_token,
    get_user_by_username,
)

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse, summary="用户注册")
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """注册新用户。用户名 3-50 字符，密码至少 6 位。"""
    # 检查用户名是否已存在
    existing = get_user_by_username(db, user_data.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被占用",
        )
    user = register_user(db, user_data)
    return user


@router.post("/login", response_model=TokenResponse, summary="用户登录")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """用户名密码登录，返回 JWT token。"""
    user = authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    access_token = create_access_token(user.id)
    return TokenResponse(access_token=access_token, user=user)


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
def me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户的信息。"""
    return current_user
