"""
认证服务：密码哈希、JWT 令牌、用户注册与认证。
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.schemas.auth import UserRegister

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """对密码进行 bcrypt 哈希。"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码与哈希是否匹配。"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int) -> str:
    """创建 JWT access token。"""
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_access_token_expire_hours)
    to_encode = {"sub": str(user_id), "exp": expire}
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[int]:
    """解析 JWT token，返回 user_id，失败返回 None。"""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            return None
        return int(user_id_str)
    except JWTError:
        return None


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """根据 ID 获取用户。"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """根据用户名获取用户。"""
    return db.query(User).filter(User.username == username).first()


def register_user(db: Session, user_data: UserRegister) -> User:
    """注册新用户，返回 User 对象。"""
    hashed = hash_password(user_data.password)
    db_user = User(
        username=user_data.username.strip(),
        password_hash=hashed,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """验证用户名密码，成功返回 User，失败返回 None。"""
    user = get_user_by_username(db, username.strip())
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    # 更新最后登录时间
    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user
