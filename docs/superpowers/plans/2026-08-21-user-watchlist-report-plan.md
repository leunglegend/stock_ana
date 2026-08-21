# 用户系统 + 自选股持久化 + 盘后复盘 + 消息中心 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为股票分析平台添加用户系统、自选股云端同步、盘后 AI 自动复盘和消息通知功能。

**Architecture:** 基于 SQLite + SQLAlchemy 的数据持久化方案，JWT 做用户鉴权，APScheduler 做定时任务。四个子系统按依赖关系分阶段实现：数据库基础设施 → 用户系统 → 自选股持久化 → 盘后复盘 → 消息中心 → 前端集成。

**Tech Stack:** FastAPI, SQLAlchemy 2.x (同步), SQLite, passlib[bcrypt], python-jose, APScheduler, Vue 3, Pinia, Element Plus

**Spec:** `docs/superpowers/specs/2026-08-21-user-watchlist-report-design.md`

## Global Constraints

- 数据库：SQLite + SQLAlchemy 2.x 同步 API
- JWT 算法：HS256，默认有效期 24 小时
- 密码哈希：bcrypt
- 定时任务：APScheduler，Cron `30 15 * * 1-5`，时区 Asia/Shanghai
- 前端：Vue 3 + Element Plus + Pinia，保持现有代码风格
- 后端代码风格：每个文件有模块 docstring，使用 Pydantic 2.x 模型
- 现有代码不做破坏性变更，未登录用户继续可用 localStorage 自选股

---

## Phase 1: 数据库基础设施 + 配置

### Task 1.1: 新增依赖 + 配置项

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/app/config.py`
- Modify: `backend/.env.example`

**Interfaces:**
- Produces: `settings.database_url`, `settings.jwt_secret_key`, `settings.jwt_algorithm`, `settings.jwt_access_token_expire_hours`, `settings.scheduler_enabled`, `settings.daily_report_cron`

- [ ] **Step 1: 更新 requirements.txt**

在 `backend/requirements.txt` 末尾追加：
```
sqlalchemy>=2.0.0
passlib[bcrypt]>=1.7.4
python-jose[cryptography]>=3.3.0
apscheduler>=3.10.0
```

- [ ] **Step 2: 更新 config.py，添加新配置项**

在 `backend/app/config.py` 的 `Settings` 类中添加：
```python
database_url: str = "sqlite:///./stock_analyzer.db"
jwt_secret_key: str = ""
jwt_algorithm: str = "HS256"
jwt_access_token_expire_hours: int = 24
scheduler_enabled: bool = True
daily_report_cron: str = "30 15 * * 1-5"
```

注意：`jwt_secret_key` 留空表示未配置，实际使用时必须设置。
在 `model_config` 中确保这些字段从环境变量读取（`JWT_SECRET_KEY` 等）。

- [ ] **Step 3: 更新 .env.example**

在 `backend/.env.example` 末尾追加：
```
# Database
DATABASE_URL=sqlite:///./stock_analyzer.db

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_HOURS=24

# Scheduler
SCHEDULER_ENABLED=true
DAILY_REPORT_CRON=30 15 * * 1-5
```

- [ ] **Step 4: 安装新依赖**
```bash
cd backend && source venv/bin/activate && pip install "sqlalchemy>=2.0.0" "passlib[bcrypt]>=1.7.4" "python-jose[cryptography]>=3.3.0" "apscheduler>=3.10.0"
```

- [ ] **Step 5: 验证配置能正常加载**

运行 Python 验证 settings 能正常实例化：
```bash
cd backend && source venv/bin/activate && python -c "from app.config import settings; print('DB:', settings.database_url); print('JWT algo:', settings.jwt_algorithm)"
```
Expected: 无报错，正确打印配置值。

---

### Task 1.2: 数据库初始化 + Base Model

**Files:**
- Create: `backend/app/database.py`
- Create: `backend/app/models/__init__.py` (更新)
- Modify: `backend/app/main.py`

**Interfaces:**
- Produces: `engine`, `SessionLocal`, `Base` (from database.py)；`get_db()` 依赖函数

- [ ] **Step 1: 创建 database.py**

```python
"""
数据库连接与会话管理。

使用 SQLAlchemy 2.x 同步 API，SQLite 作为默认数据库。
提供 engine、SessionLocal 和 Base，以及 get_db 依赖函数。
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# SQLite 连接需要 check_same_thread=False
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI 依赖：获取数据库会话，自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 2: 在 main.py 中添加启动时建表逻辑**

在 `main.py` 的 `preload_data()` 或启动事件中，在最前面加：
```python
from app.database import Base, engine
# 导入所有模型，确保 Base.metadata 能找到它们
from app.models import user, watchlist, report, notification  # noqa: F401

Base.metadata.create_all(bind=engine)
```

注意：这行要放在启动预加载的最开始（模型文件先建好后再加，现在先写注释占位，等 Phase 2 模型建好后启用）。

- [ ] **Step 3: 验证数据库模块能正常导入**
```bash
cd backend && source venv/bin/activate && python -c "from app.database import engine, SessionLocal, Base, get_db; print('database module OK')"
```
Expected: 无报错。

---

## Phase 2: 用户系统（后端）

### Task 2.1: User ORM Model + Pydantic Schema

**Files:**
- Create: `backend/app/models/user.py`
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/schemas/__init__.py`

**Interfaces:**
- Produces: `User` ORM model；`UserRegister`, `UserLogin`, `UserResponse`, `TokenResponse` Pydantic models

- [ ] **Step 1: 创建 User ORM 模型**

```python
"""
用户数据模型。
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
```

- [ ] **Step 2: 创建 Pydantic schemas**

创建 `backend/app/schemas/__init__.py`：
```python
"""
Pydantic 数据模型包。
"""
```

创建 `backend/app/schemas/auth.py`：
```python
"""
认证相关 Pydantic 模型。
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")


class UserLogin(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
```

- [ ] **Step 3: 在 models/__init__.py 中导出 User**

编辑 `backend/app/models/__init__.py`（当前为空）：
```python
"""
SQLAlchemy ORM 模型包。
"""

from app.models.user import User
```

- [ ] **Step 4: 验证模型能正常导入**
```bash
cd backend && source venv/bin/activate && python -c "from app.models.user import User; from app.schemas.auth import UserRegister, UserResponse, TokenResponse; print('user models OK')"
```
Expected: 无报错。

---

### Task 2.2: Auth Service（密码哈希 + JWT + 用户 CRUD）

**Files:**
- Create: `backend/app/services/auth_service.py`
- Create: `backend/app/dependencies.py`

**Interfaces:**
- Produces: `hash_password()`, `verify_password()`, `create_access_token()`, `register_user()`, `authenticate_user()`, `get_user_by_id()`, `get_current_user()` 依赖

- [ ] **Step 1: 创建 auth_service.py**

```python
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
```

- [ ] **Step 2: 创建 dependencies.py**

```python
"""
FastAPI 依赖注入集合。
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth_service import decode_access_token, get_user_by_id
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """获取当前登录用户。未登录或 token 无效则抛出 401。"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    user_id = decode_access_token(token)
    if user_id is None:
        raise credentials_exception

    user = get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception

    return user


def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """获取当前登录用户（可选）。未登录返回 None，不抛异常。"""
    if not token:
        return None
    user_id = decode_access_token(token)
    if user_id is None:
        return None
    return get_user_by_id(db, user_id)
```

- [ ] **Step 3: 验证密码哈希和 JWT 功能**
```bash
cd backend && source venv/bin/activate && python -c "
from app.services.auth_service import hash_password, verify_password, create_access_token, decode_access_token
# 测试密码
h = hash_password('test123456')
assert verify_password('test123456', h)
assert not verify_password('wrong', h)
# 测试 JWT (需要设置 JWT_SECRET_KEY)
import os
os.environ['JWT_SECRET_KEY'] = 'test-secret-key-for-unit-test'
from app.config import settings
print('JWT secret set:', bool(settings.jwt_secret_key))
token = create_access_token(123)
uid = decode_access_token(token)
assert uid == 123, f'Expected 123, got {uid}'
print('auth_service tests passed')
"
```
Expected: 全部通过，打印 `auth_service tests passed`。

---

### Task 2.3: Auth API 路由

**Files:**
- Create: `backend/app/routes/auth.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/database.py`（确保建表）

**Interfaces:**
- Produces: `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`

- [ ] **Step 1: 创建 auth.py 路由**

```python
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
```

- [ ] **Step 2: 在 main.py 中注册 auth 路由并启用建表**

在 `main.py` 中：
- 添加 `from app.routes.auth import router as auth_router`
- 在路由注册处添加 `app.include_router(auth_router)`
- 在启动函数的最开始（preload 之前）添加 `Base.metadata.create_all(bind=engine)`（从 `app.database` 导入），并确保导入了所有模型文件

- [ ] **Step 3: 启动后端验证 API 可用**
```bash
cd backend && source venv/bin/activate && uvicorn app.main:app --port 8000 &
sleep 3
# 测试注册
curl -s -X POST http://localhost:8000/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"testuser","password":"test123456"}' | python -m json.tool
# 测试登录
curl -s -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"testuser","password":"test123456"}' | python -m json.tool
# 测试 /me (用登录返回的 token)
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login -H 'Content-Type: application/json' -d '{"username":"testuser","password":"test123456"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
curl -s http://localhost:8000/api/auth/me -H "Authorization: Bearer $TOKEN" | python -m json.tool
# 关掉 uvicorn
kill %1
```
Expected: 三个接口都正常返回 JSON，注册返回用户信息，登录返回 token+user，/me 返回当前用户。

---

## Phase 3: 自选股持久化（后端）

### Task 3.1: Watchlist ORM Models + Schemas

**Files:**
- Create: `backend/app/models/watchlist.py`
- Create: `backend/app/schemas/watchlist.py`
- Modify: `backend/app/models/__init__.py`

**Interfaces:**
- Produces: `WatchlistGroup`, `WatchlistItem` ORM models；相应的 Pydantic schemas

- [ ] **Step 1: 创建 watchlist.py ORM 模型**

```python
"""
自选股数据模型：分组 + 明细。
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.database import Base


class WatchlistGroup(Base):
    __tablename__ = "watchlist_groups"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    stocks = relationship("WatchlistItem", back_populates="group", cascade="all, delete-orphan", order_by="WatchlistItem.sort_order")

    __table_args__ = (
        Index("idx_group_user_sort", "user_id", "sort_order"),
    )


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("watchlist_groups.id"), nullable=False, index=True)
    stock_code = Column(String(10), nullable=False)
    stock_name = Column(String(20), nullable=False)
    cost = Column(Float, default=0.0)
    remark = Column(String(200), default="")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    group = relationship("WatchlistGroup", back_populates="stocks")

    __table_args__ = (
        Index("idx_item_group_sort", "group_id", "sort_order"),
    )
```

- [ ] **Step 2: 创建 watchlist schemas**

```python
"""
自选股相关 Pydantic 模型。
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class WatchlistItemBase(BaseModel):
    stock_code: str = Field(..., max_length=10)
    stock_name: str = Field(..., max_length=20)
    cost: float = 0.0
    remark: str = ""


class WatchlistItemCreate(WatchlistItemBase):
    group_id: int


class WatchlistItemUpdate(BaseModel):
    cost: Optional[float] = None
    remark: Optional[str] = None


class WatchlistItemResponse(WatchlistItemBase):
    id: int
    group_id: int
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class WatchlistGroupBase(BaseModel):
    name: str = Field(..., max_length=50)


class WatchlistGroupCreate(WatchlistGroupBase):
    pass


class WatchlistGroupUpdate(BaseModel):
    name: Optional[str] = None


class WatchlistGroupResponse(WatchlistGroupBase):
    id: int
    user_id: int
    sort_order: int
    created_at: datetime
    stocks: List[WatchlistItemResponse] = []

    model_config = {"from_attributes": True}


class WatchlistSyncGroup(BaseModel):
    """同步用的分组数据（从 localStorage 导入）。"""
    id: str  # 前端的临时 id
    name: str
    stocks: List[WatchlistItemBase] = []


class WatchlistSyncRequest(BaseModel):
    groups: List[WatchlistSyncGroup]
    replace: bool = False  # 是否替换现有数据
```

- [ ] **Step 3: 在 models/__init__.py 中导出模型**

在 `backend/app/models/__init__.py` 中添加：
```python
from app.models.watchlist import WatchlistGroup, WatchlistItem
```

- [ ] **Step 4: 验证模型能正常导入**
```bash
cd backend && source venv/bin/activate && python -c "from app.models.watchlist import WatchlistGroup, WatchlistItem; from app.schemas.watchlist import WatchlistGroupResponse, WatchlistSyncRequest; print('watchlist models OK')"
```
Expected: 无报错。

---

### Task 3.2: Watchlist Service + API 路由

**Files:**
- Create: `backend/app/services/watchlist_service.py`
- Create: `backend/app/routes/watchlist.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Produces: 自选股 CRUD service 函数；`GET/POST/PUT/DELETE /api/watchlist/*` REST API

- [ ] **Step 1: 创建 watchlist_service.py**

```python
"""
自选股服务：分组和股票的增删改查。
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.watchlist import WatchlistGroup, WatchlistItem
from app.schemas.watchlist import (
    WatchlistGroupCreate,
    WatchlistGroupUpdate,
    WatchlistItemCreate,
    WatchlistItemUpdate,
    WatchlistSyncRequest,
)


# ---------- 分组 ----------

def get_groups_with_stocks(db: Session, user_id: int) -> List[WatchlistGroup]:
    """获取用户所有分组及其下的股票，按 sort_order 排序。"""
    groups = (
        db.query(WatchlistGroup)
        .filter(WatchlistGroup.user_id == user_id)
        .order_by(WatchlistGroup.sort_order, WatchlistGroup.id)
        .all()
    )
    return groups


def create_group(db: Session, user_id: int, data: WatchlistGroupCreate) -> WatchlistGroup:
    """创建新分组。"""
    # 计算最大 sort_order
    max_order = (
        db.query(WatchlistGroup)
        .filter(WatchlistGroup.user_id == user_id)
        .count()
    )
    group = WatchlistGroup(
        user_id=user_id,
        name=data.name.strip(),
        sort_order=max_order,
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def update_group(db: Session, user_id: int, group_id: int, data: WatchlistGroupUpdate) -> Optional[WatchlistGroup]:
    """更新分组名称。"""
    group = db.query(WatchlistGroup).filter(
        WatchlistGroup.id == group_id,
        WatchlistGroup.user_id == user_id,
    ).first()
    if not group:
        return None
    if data.name is not None:
        group.name = data.name.strip()
    db.commit()
    db.refresh(group)
    return group


def delete_group(db: Session, user_id: int, group_id: int) -> bool:
    """删除分组（及其下所有股票）。"""
    group = db.query(WatchlistGroup).filter(
        WatchlistGroup.id == group_id,
        WatchlistGroup.user_id == user_id,
    ).first()
    if not group:
        return False
    db.delete(group)
    db.commit()
    return True


# ---------- 股票 ----------

def add_item(db: Session, user_id: int, data: WatchlistItemCreate) -> Optional[WatchlistItem]:
    """向分组添加股票。如果已存在则返回 None。"""
    # 验证分组属于该用户
    group = db.query(WatchlistGroup).filter(
        WatchlistGroup.id == data.group_id,
        WatchlistGroup.user_id == user_id,
    ).first()
    if not group:
        return None

    # 检查是否已存在
    existing = db.query(WatchlistItem).filter(
        WatchlistItem.group_id == data.group_id,
        WatchlistItem.stock_code == data.stock_code,
    ).first()
    if existing:
        return None

    max_order = db.query(WatchlistItem).filter(WatchlistItem.group_id == data.group_id).count()
    item = WatchlistItem(
        group_id=data.group_id,
        stock_code=data.stock_code,
        stock_name=data.stock_name,
        cost=data.cost,
        remark=data.remark,
        sort_order=max_order,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_item(db: Session, user_id: int, item_id: int, data: WatchlistItemUpdate) -> Optional[WatchlistItem]:
    """更新自选股（成本/备注）。"""
    item = (
        db.query(WatchlistItem)
        .join(WatchlistGroup)
        .filter(
            WatchlistItem.id == item_id,
            WatchlistGroup.user_id == user_id,
        )
        .first()
    )
    if not item:
        return None
    if data.cost is not None:
        item.cost = data.cost
    if data.remark is not None:
        item.remark = data.remark
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, user_id: int, item_id: int) -> bool:
    """删除自选股。"""
    item = (
        db.query(WatchlistItem)
        .join(WatchlistGroup)
        .filter(
            WatchlistItem.id == item_id,
            WatchlistGroup.user_id == user_id,
        )
        .first()
    )
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True


# ---------- 同步 ----------

def sync_watchlist(db: Session, user_id: int, data: WatchlistSyncRequest) -> List[WatchlistGroup]:
    """批量同步自选股（从 localStorage 导入）。"""
    if data.replace:
        # 清空现有数据
        db.query(WatchlistGroup).filter(WatchlistGroup.user_id == user_id).delete()
        db.commit()

    for i, g in enumerate(data.groups):
        group = WatchlistGroup(
            user_id=user_id,
            name=g.name.strip(),
            sort_order=i,
        )
        db.add(group)
        db.flush()  # 获取 group.id

        for j, s in enumerate(g.stocks):
            item = WatchlistItem(
                group_id=group.id,
                stock_code=s.stock_code,
                stock_name=s.stock_name,
                cost=s.cost,
                remark=s.remark,
                sort_order=j,
            )
            db.add(item)

    db.commit()
    return get_groups_with_stocks(db, user_id)


def get_user_watchlist_stocks(db: Session, user_id: int) -> List[tuple]:
    """获取用户所有自选股的 (code, name) 列表，用于复盘任务。"""
    items = (
        db.query(WatchlistItem.stock_code, WatchlistItem.stock_name)
        .join(WatchlistGroup)
        .filter(WatchlistGroup.user_id == user_id)
        .distinct(WatchlistItem.stock_code)
        .all()
    )
    return [(row.stock_code, row.stock_name) for row in items]
```

- [ ] **Step 2: 创建 watchlist.py 路由**

```python
"""
自选股相关 API 路由。
所有接口需登录。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.watchlist import (
    WatchlistGroupCreate,
    WatchlistGroupUpdate,
    WatchlistGroupResponse,
    WatchlistItemCreate,
    WatchlistItemUpdate,
    WatchlistItemResponse,
    WatchlistSyncRequest,
)
from app.services import watchlist_service

router = APIRouter(prefix="/api/watchlist", tags=["自选股"])


# ---------- 分组 ----------

@router.get("/groups", response_model=List[WatchlistGroupResponse], summary="获取自选股分组列表")
def list_groups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户所有分组（含分组下的股票）。"""
    groups = watchlist_service.get_groups_with_stocks(db, current_user.id)
    return groups


@router.post("/groups", response_model=WatchlistGroupResponse, summary="新建分组")
def create_group(
    data: WatchlistGroupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = watchlist_service.create_group(db, current_user.id, data)
    return group


@router.put("/groups/{group_id}", response_model=WatchlistGroupResponse, summary="更新分组")
def update_group(
    group_id: int,
    data: WatchlistGroupUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = watchlist_service.update_group(db, current_user.id, group_id, data)
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    return group


@router.delete("/groups/{group_id}", summary="删除分组")
def delete_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    success = watchlist_service.delete_group(db, current_user.id, group_id)
    if not success:
        raise HTTPException(status_code=404, detail="分组不存在")
    return {"success": True}


# ---------- 股票 ----------

@router.post("/items", response_model=WatchlistItemResponse, summary="添加自选股")
def add_item(
    data: WatchlistItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = watchlist_service.add_item(db, current_user.id, data)
    if not item:
        raise HTTPException(status_code=400, detail="添加失败：分组不存在或股票已在列表中")
    return item


@router.put("/items/{item_id}", response_model=WatchlistItemResponse, summary="更新自选股")
def update_item(
    item_id: int,
    data: WatchlistItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = watchlist_service.update_item(db, current_user.id, item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="自选股不存在")
    return item


@router.delete("/items/{item_id}", summary="删除自选股")
def delete_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    success = watchlist_service.delete_item(db, current_user.id, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="自选股不存在")
    return {"success": True}


# ---------- 同步 ----------

@router.post("/sync", response_model=List[WatchlistGroupResponse], summary="批量同步自选股")
def sync_watchlist(
    data: WatchlistSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """从客户端批量导入自选股（用于首次登录同步 localStorage 数据）。"""
    groups = watchlist_service.sync_watchlist(db, current_user.id, data)
    return groups
```

- [ ] **Step 3: 在 main.py 中注册 watchlist 路由**

添加 `from app.routes.watchlist import router as watchlist_router` 和 `app.include_router(watchlist_router)`。

- [ ] **Step 4: 启动后端验证自选股 API**
```bash
cd backend && source venv/bin/activate && uvicorn app.main:app --port 8000 &
sleep 3
# 登录获取 token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login -H 'Content-Type: application/json' -d '{"username":"testuser","password":"test123456"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "Token: $TOKEN"
# 获取分组（应该为空）
curl -s http://localhost:8000/api/watchlist/groups -H "Authorization: Bearer $TOKEN" | python -m json.tool
# 创建分组
curl -s -X POST http://localhost:8000/api/watchlist/groups \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"name":"我的自选"}' | python -m json.tool
# 添加股票 (用上面返回的 group id)
curl -s -X POST http://localhost:8000/api/watchlist/items \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"group_id":1,"stock_code":"600519","stock_name":"贵州茅台","cost":1700.0}' | python -m json.tool
# 再获取分组验证
curl -s http://localhost:8000/api/watchlist/groups -H "Authorization: Bearer $TOKEN" | python -m json.tool
kill %1
```
Expected: 全部 API 正常返回，最终分组列表中包含贵州茅台。

---

## Phase 4: 盘后复盘 + 消息中心（后端）

### Task 4.1: Report + Notification ORM Models + Schemas

**Files:**
- Create: `backend/app/models/report.py`
- Create: `backend/app/models/notification.py`
- Create: `backend/app/schemas/report.py`
- Create: `backend/app/schemas/notification.py`
- Modify: `backend/app/models/__init__.py`

**Interfaces:**
- Produces: `DailyReport`, `StockReport`, `Notification` ORM models；相应 Pydantic schemas

- [ ] **Step 1: 创建 report.py ORM 模型**

```python
"""
复盘报告数据模型：日报 + 个股分析。
"""

from datetime import datetime, date

from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Text, JSON, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    report_date = Column(Date, nullable=False)
    market_summary = Column(Text, default="")
    highlights = Column(JSON, default=list)  # [{stock_code, stock_name, reason}]
    risk_notes = Column(Text, default="")
    status = Column(String(20), default="pending")  # pending / generating / completed / failed
    stock_count = Column(Integer, default=0)
    error_msg = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    stock_reports = relationship("StockReport", back_populates="daily_report", cascade="all, delete-orphan", order_by="StockReport.change_pct.desc()")

    __table_args__ = (
        Index("idx_report_user_date", "user_id", "report_date"),
        UniqueConstraint("user_id", "report_date", name="uq_user_report_date"),
    )


class StockReport(Base):
    __tablename__ = "stock_reports"

    id = Column(Integer, primary_key=True, index=True)
    daily_report_id = Column(Integer, ForeignKey("daily_reports.id"), nullable=False, index=True)
    stock_code = Column(String(10), nullable=False)
    stock_name = Column(String(20), nullable=False)
    change_pct = Column(Float, default=0.0)
    close_price = Column(Float, default=0.0)
    analysis_text = Column(Text, default="")
    summary = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    daily_report = relationship("DailyReport", back_populates="stock_reports")
```

- [ ] **Step 2: 创建 notification.py ORM 模型**

```python
"""
通知消息数据模型。
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index

from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(100), nullable=False)
    content = Column(String(500), default="")
    type = Column(String(20), default="system")  # report / system
    ref_id = Column(Integer, nullable=True)  # 关联 ID，如 report_id
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_notif_user_read_time", "user_id", "is_read", "created_at"),
    )
```

- [ ] **Step 3: 创建 report schemas**

```python
"""
复盘报告相关 Pydantic 模型。
"""

from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel


class StockReportResponse(BaseModel):
    id: int
    daily_report_id: int
    stock_code: str
    stock_name: str
    change_pct: float
    close_price: float
    analysis_text: str
    summary: str
    created_at: datetime

    model_config = {"from_attributes": True}


class HighlightItem(BaseModel):
    stock_code: str
    stock_name: str
    reason: str


class DailyReportResponse(BaseModel):
    id: int
    user_id: int
    report_date: date
    market_summary: str
    highlights: List[HighlightItem] = []
    risk_notes: str
    status: str
    stock_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    stock_reports: List[StockReportResponse] = []

    model_config = {"from_attributes": True}


class DailyReportListItem(BaseModel):
    """列表页用的精简版，不包含 stock_reports 详情。"""
    id: int
    report_date: date
    status: str
    stock_count: int
    market_summary: str  # 截断版或完整版
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PaginatedDailyReports(BaseModel):
    items: List[DailyReportListItem]
    total: int
    page: int
    page_size: int
```

- [ ] **Step 4: 创建 notification schemas**

```python
"""
通知相关 Pydantic 模型。
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    title: str
    content: str
    type: str
    ref_id: Optional[int] = None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedNotifications(BaseModel):
    items: List[NotificationResponse]
    total: int
    page: int
    page_size: int


class UnreadCountResponse(BaseModel):
    count: int
```

- [ ] **Step 5: 更新 models/__init__.py**

添加 `report.py` 和 `notification.py` 的导入。

- [ ] **Step 6: 验证模型能正常导入**
```bash
cd backend && source venv/bin/activate && python -c "
from app.models.report import DailyReport, StockReport
from app.models.notification import Notification
from app.schemas.report import DailyReportResponse, PaginatedDailyReports
from app.schemas.notification import NotificationResponse, UnreadCountResponse
print('report + notification models OK')
"
```
Expected: 无报错。

---

### Task 4.2: Report Service（AI 复盘生成逻辑）

**Files:**
- Create: `backend/app/services/report_service.py`

**Interfaces:**
- Produces: `generate_daily_report_for_user()`, `get_reports()`, `get_report_detail()`, `get_report_by_date()` 等函数

- [ ] **Step 1: 创建 report_service.py**

```python
"""
盘后复盘报告服务：生成 + 查询。
"""

import json
import logging
from datetime import date, datetime
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.report import DailyReport, StockReport
from app.models.watchlist import WatchlistGroup, WatchlistItem
from app.services import watchlist_service

logger = logging.getLogger(__name__)


def get_reports(
    db: Session, user_id: int, page: int = 1, page_size: int = 20
) -> Tuple[List[DailyReport], int]:
    """分页获取用户的复盘报告列表。"""
    query = db.query(DailyReport).filter(DailyReport.user_id == user_id)
    total = query.count()
    items = (
        query.order_by(DailyReport.report_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def get_report_detail(db: Session, user_id: int, report_id: int) -> Optional[DailyReport]:
    """获取报告详情（含个股分析）。"""
    report = (
        db.query(DailyReport)
        .filter(DailyReport.id == report_id, DailyReport.user_id == user_id)
        .first()
    )
    return report


def get_report_by_date(db: Session, user_id: int, report_date: date) -> Optional[DailyReport]:
    """根据日期获取报告。"""
    return (
        db.query(DailyReport)
        .filter(DailyReport.user_id == user_id, DailyReport.report_date == report_date)
        .first()
    )


def get_all_users_with_watchlist(db: Session) -> List[int]:
    """获取所有有自选股的用户 ID 列表（用于定时任务遍历）。"""
    user_ids = (
        db.query(WatchlistGroup.user_id)
        .join(WatchlistItem, WatchlistItem.group_id == WatchlistGroup.id)
        .distinct()
        .all()
    )
    return [row[0] for row in user_ids]


def create_pending_report(db: Session, user_id: int, report_date: date) -> DailyReport:
    """创建一个 pending 状态的报告记录。"""
    # 检查是否已存在
    existing = get_report_by_date(db, user_id, report_date)
    if existing:
        # 重置为 pending，重新生成
        existing.status = "pending"
        existing.market_summary = ""
        existing.highlights = []
        existing.risk_notes = ""
        existing.error_msg = ""
        existing.stock_count = 0
        existing.completed_at = None
        # 删除旧的个股分析
        db.query(StockReport).filter(StockReport.daily_report_id == existing.id).delete()
        db.commit()
        db.refresh(existing)
        return existing

    report = DailyReport(
        user_id=user_id,
        report_date=report_date,
        status="pending",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def update_report_status(
    db: Session, report_id: int, status: str, error_msg: str = ""
) -> None:
    """更新报告状态。"""
    report = db.query(DailyReport).filter(DailyReport.id == report_id).first()
    if report:
        report.status = status
        if error_msg:
            report.error_msg = error_msg
        if status == "completed":
            report.completed_at = datetime.utcnow()
        db.commit()


def save_stock_report(
    db: Session,
    daily_report_id: int,
    stock_code: str,
    stock_name: str,
    change_pct: float,
    close_price: float,
    analysis_text: str,
    summary: str,
) -> StockReport:
    """保存个股分析结果。"""
    item = StockReport(
        daily_report_id=daily_report_id,
        stock_code=stock_code,
        stock_name=stock_name,
        change_pct=change_pct,
        close_price=close_price,
        analysis_text=analysis_text,
        summary=summary,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    # 更新日报 stock_count
    report = db.query(DailyReport).filter(DailyReport.id == daily_report_id).first()
    if report:
        report.stock_count = (
            db.query(StockReport).filter(StockReport.daily_report_id == daily_report_id).count()
        )
        db.commit()
    return item


def save_report_summary(
    db: Session,
    report_id: int,
    market_summary: str,
    highlights: List[dict],
    risk_notes: str,
) -> None:
    """保存报告的整体分析（市场总览 + 关注重点 + 风险提示）。"""
    report = db.query(DailyReport).filter(DailyReport.id == report_id).first()
    if report:
        report.market_summary = market_summary
        report.highlights = highlights
        report.risk_notes = risk_notes
        db.commit()


async def generate_daily_report_for_user(
    db: Session, user_id: int, report_date: date
) -> Optional[DailyReport]:
    """
    为指定用户生成一天的复盘报告。
    这是核心生成函数，返回生成好的报告，失败返回 None。

    流程：
    1. 获取用户自选股
    2. 创建 pending report
    3. 获取市场概览数据
    4. 逐只股票获取行情 + K 线 + AI 分析
    5. 生成整体市场点评 + 关注重点
    6. 标记 completed
    """
    from app.services.stock_data import get_stock_quote, get_kline_data
    from app.services.market_data import get_market_summary
    from app.services.ai_analyst import generate_stock_daily_analysis, generate_daily_report_overview

    # 1. 获取自选股
    stocks = watchlist_service.get_user_watchlist_stocks(db, user_id)
    if not stocks:
        logger.info(f"用户 {user_id} 没有自选股，跳过复盘生成")
        return None

    # 2. 创建 pending report
    report = create_pending_report(db, user_id, report_date)
    report.status = "generating"
    db.commit()

    try:
        # 3. 获取市场概览
        try:
            market_data = await get_market_summary()
        except Exception as e:
            logger.warning(f"获取市场概览失败: {e}")
            market_data = None

        # 4. 逐只股票分析
        stock_results = []
        for stock_code, stock_name in stocks:
            try:
                # 获取行情
                quote = await get_stock_quote(stock_code)
                change_pct = getattr(quote, "change_percent", 0) or 0.0
                close_price = getattr(quote, "current_price", 0) or 0.0

                # 获取近 30 日 K 线
                try:
                    kline = await get_kline_data(stock_code, period="daily", days=30)
                except Exception:
                    kline = None

                # AI 分析
                analysis_text, summary = await generate_stock_daily_analysis(
                    stock_code, stock_name, quote, kline
                )

                # 保存
                save_stock_report(
                    db, report.id, stock_code, stock_name,
                    change_pct, close_price, analysis_text, summary
                )
                stock_results.append({
                    "stock_code": stock_code,
                    "stock_name": stock_name,
                    "change_pct": change_pct,
                    "summary": summary,
                })

            except Exception as e:
                logger.error(f"分析股票 {stock_code} 失败: {e}")
                continue

        if not stock_results:
            update_report_status(db, report.id, "failed", "所有股票分析均失败")
            return None

        # 5. 生成整体复盘
        try:
            market_summary_text, highlights, risk_notes = await generate_daily_report_overview(
                stock_results, market_data
            )
            save_report_summary(db, report.id, market_summary_text, highlights, risk_notes)
        except Exception as e:
            logger.warning(f"生成整体复盘失败: {e}")
            # 整体失败不影响个股结果，留空即可

        # 6. 标记完成
        update_report_status(db, report.id, "completed")
        db.refresh(report)
        return report

    except Exception as e:
        logger.error(f"生成复盘报告失败 (user={user_id}, date={report_date}): {e}")
        update_report_status(db, report.id, "failed", str(e)[:500])
        return None
```

- [ ] **Step 2: 验证 report_service 能正常导入**
```bash
cd backend && source venv/bin/activate && python -c "from app.services.report_service import get_reports, get_report_detail; print('report_service OK')"
```
Expected: 无报错。

---

### Task 4.3: AI 分析扩展（盘后版 prompt）

**Files:**
- Modify: `backend/app/services/ai_analyst.py`

**Interfaces:**
- Produces: `generate_stock_daily_analysis()`, `generate_daily_report_overview()` 异步函数

- [ ] **Step 1: 在 ai_analyst.py 中添加盘后分析函数**

添加两个新函数：

**`generate_stock_daily_analysis(stock_code, stock_name, quote, kline)`**
- 角色：盘后个股分析师
- 输入：股票基本信息、当日行情、近30日 K线
- 输出：返回 `(analysis_text, summary)` 二元组
  - `analysis_text`：300-500 字 Markdown 分析，包含当日表现点评、短期技术面判断、关注点位
  - `summary`：一句话摘要（50 字以内）
- 系统 prompt 要点：聚焦当日表现，结合近期走势，给出明确的观察点，必须有风险提示

**`generate_daily_report_overview(stock_results, market_data)`**
- 输入：股票分析结果列表（含 code, name, change_pct, summary）、市场概览数据
- 输出：返回 `(market_summary, highlights, risk_notes)` 三元组
  - `market_summary`：200-300 字市场总评
  - `highlights`：3-5 只重点关注股票数组，每只含 `{stock_code, stock_name, reason}`
  - `risk_notes`：100-200 字整体风险提示
- 系统 prompt 要点：从自选股中挑选最值得关注的标的，整体把握市场情绪，风险提示要客观

两个函数都使用 `client.messages.create()`（非流式），等待完整返回后解析。
优先用与现有 `analyze_stock()` 相同的模型配置。

- [ ] **Step 2: 验证 AI 函数能正常导入**
```bash
cd backend && source venv/bin/activate && python -c "from app.services.ai_analyst import generate_stock_daily_analysis, generate_daily_report_overview; print('AI functions imported OK')"
```
Expected: 无报错（不需要实际调用，只需语法正确）。

---

### Task 4.4: Notification Service + API

**Files:**
- Create: `backend/app/services/notification_service.py`
- Create: `backend/app/routes/notification.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Produces: 通知 CRUD 函数；`GET /api/notifications`, `PUT /api/notifications/{id}/read`, `PUT /api/notifications/read-all`, `GET /api/notifications/unread-count`

- [ ] **Step 1: 创建 notification_service.py**

```python
"""
通知服务：站内信管理。
"""

from typing import List, Tuple

from sqlalchemy.orm import Session

from app.models.notification import Notification


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    content: str = "",
    type: str = "system",
    ref_id: int | None = None,
) -> Notification:
    """创建一条通知。"""
    notif = Notification(
        user_id=user_id,
        title=title,
        content=content,
        type=type,
        ref_id=ref_id,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


def get_notifications(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    unread_only: bool = False,
) -> Tuple[List[Notification], int]:
    """分页获取通知列表。"""
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if unread_only:
        query = query.filter(Notification.is_read == False)  # noqa: E712
    total = query.count()
    items = (
        query.order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def get_unread_count(db: Session, user_id: int) -> int:
    """获取未读通知数量。"""
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
        .count()
    )


def mark_as_read(db: Session, user_id: int, notif_id: int) -> bool:
    """标记单条通知为已读。"""
    notif = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.user_id == user_id,
    ).first()
    if not notif:
        return False
    notif.is_read = True
    db.commit()
    return True


def mark_all_as_read(db: Session, user_id: int) -> int:
    """标记所有通知为已读，返回已读数量。"""
    count = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
        .update({Notification.is_read: True})
    )
    db.commit()
    return count
```

- [ ] **Step 2: 创建 notification.py 路由**

```python
"""
通知相关 API 路由。
所有接口需登录。
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.notification import (
    NotificationResponse,
    PaginatedNotifications,
    UnreadCountResponse,
)
from app.services import notification_service

router = APIRouter(prefix="/api/notifications", tags=["通知"])


@router.get("", response_model=PaginatedNotifications, summary="获取通知列表")
def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = notification_service.get_notifications(
        db, current_user.id, page, page_size, unread_only
    )
    return PaginatedNotifications(
        items=items, total=total, page=page, page_size=page_size
    )


@router.get("/unread-count", response_model=UnreadCountResponse, summary="未读数量")
def unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    count = notification_service.get_unread_count(db, current_user.id)
    return UnreadCountResponse(count=count)


@router.put("/{notif_id}/read", response_model=NotificationResponse, summary="标记已读")
def mark_read(
    notif_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from fastapi import HTTPException
    success = notification_service.mark_as_read(db, current_user.id, notif_id)
    if not success:
        raise HTTPException(status_code=404, detail="通知不存在")
    # 返回更新后的对象
    from app.models.notification import Notification
    notif = db.query(Notification).filter(Notification.id == notif_id).first()
    return notif


@router.put("/read-all", summary="全部已读")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    count = notification_service.mark_all_as_read(db, current_user.id)
    return {"success": True, "count": count}
```

- [ ] **Step 3: 在 main.py 中注册 notification 路由**

添加 `from app.routes.notification import router as notification_router` 和 `app.include_router(notification_router)`。

- [ ] **Step 4: 验证通知 API**
```bash
cd backend && source venv/bin/activate && uvicorn app.main:app --port 8000 &
sleep 3
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login -H 'Content-Type: application/json' -d '{"username":"testuser","password":"test123456"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
# 获取未读数（应该为 0）
curl -s "http://localhost:8000/api/notifications/unread-count" -H "Authorization: Bearer $TOKEN" | python -m json.tool
# 获取列表
curl -s "http://localhost:8000/api/notifications?page=1&page_size=10" -H "Authorization: Bearer $TOKEN" | python -m json.tool
kill %1
```
Expected: 正常返回 0 条记录。

---

### Task 4.5: Report API 路由

**Files:**
- Create: `backend/app/routes/report.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Produces: `GET /api/reports`, `GET /api/reports/{id}`, `POST /api/reports/generate`

- [ ] **Step 1: 创建 report.py 路由**

```python
"""
复盘报告相关 API 路由。
所有接口需登录。
"""

import asyncio
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.report import (
    DailyReportResponse,
    DailyReportListItem,
    PaginatedDailyReports,
)
from app.services import report_service, notification_service

router = APIRouter(prefix="/api/reports", tags=["复盘报告"])


@router.get("", response_model=PaginatedDailyReports, summary="复盘报告列表")
def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """分页获取当前用户的复盘报告列表。"""
    items, total = report_service.get_reports(db, current_user.id, page, page_size)
    return PaginatedDailyReports(
        items=[DailyReportListItem.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{report_id}", response_model=DailyReportResponse, summary="报告详情")
def get_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取单份复盘报告详情（含个股分析）。"""
    report = report_service.get_report_detail(db, current_user.id, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    return report


def _run_generate_task(user_id: int, report_date: date):
    """在后台线程中运行报告生成任务。"""
    import asyncio
    db = SessionLocal()
    try:
        report = asyncio.run(
            report_service.generate_daily_report_for_user(db, user_id, report_date)
        )
        if report and report.status == "completed":
            # 生成通知
            notification_service.create_notification(
                db,
                user_id=user_id,
                title=f"{report_date} 盘后复盘已生成",
                content=f"覆盖 {report.stock_count} 只自选股，点击查看详情",
                type="report",
                ref_id=report.id,
            )
    finally:
        db.close()


@router.post("/generate", summary="手动生成今日复盘")
def generate_today(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """手动触发生成今日复盘报告（后台异步执行）。"""
    today = date.today()
    # 检查是否已有 completed 的报告
    existing = report_service.get_report_by_date(db, current_user.id, today)
    if existing and existing.status == "completed":
        return {"success": True, "report_id": existing.id, "message": "今日报告已存在"}

    # 后台任务
    background_tasks.add_task(_run_generate_task, current_user.id, today)

    # 先创建 pending 记录
    report = report_service.create_pending_report(db, current_user.id, today)
    return {"success": True, "report_id": report.id, "message": "正在生成中..."}
```

- [ ] **Step 2: 在 main.py 中注册 report 路由**

添加 `from app.routes.report import router as report_router` 和 `app.include_router(report_router)`。

- [ ] **Step 3: 验证报告 API 基本可用**
```bash
cd backend && source venv/bin/activate && uvicorn app.main:app --port 8000 &
sleep 3
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login -H 'Content-Type: application/json' -d '{"username":"testuser","password":"test123456"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
# 获取报告列表
curl -s "http://localhost:8000/api/reports?page=1&page_size=10" -H "Authorization: Bearer $TOKEN" | python -m json.tool
kill %1
```
Expected: 正常返回空列表。

---

### Task 4.6: APScheduler 定时任务

**Files:**
- Create: `backend/app/services/scheduler.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Produces: `start_scheduler()`, `shutdown_scheduler()`；每日 15:30 自动触发盘后复盘

- [ ] **Step 1: 创建 scheduler.py**

```python
"""
定时任务调度器。

使用 APScheduler BackgroundScheduler，在 FastAPI 启动时启动。
主要任务：盘后复盘（交易日 15:30）
"""

import asyncio
import logging
from datetime import date

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.database import SessionLocal
from app.services import report_service, notification_service

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def run_daily_report_job():
    """
    盘后复盘定时任务。
    遍历所有有自选股的用户，为每个用户生成当日复盘报告。
    """
    logger.info("开始执行盘后复盘定时任务")
    today = date.today()

    db = SessionLocal()
    try:
        user_ids = report_service.get_all_users_with_watchlist(db)
        logger.info(f"找到 {len(user_ids)} 个有自选股的用户")

        for user_id in user_ids:
            try:
                # 检查是否已生成
                existing = report_service.get_report_by_date(db, user_id, today)
                if existing and existing.status == "completed":
                    logger.info(f"用户 {user_id} 今日报告已存在，跳过")
                    continue

                # 生成报告（同步调用 async 函数）
                report = asyncio.run(
                    report_service.generate_daily_report_for_user(db, user_id, today)
                )

                if report and report.status == "completed":
                    # 发送通知
                    notification_service.create_notification(
                        db,
                        user_id=user_id,
                        title=f"{today} 盘后复盘已生成",
                        content=f"覆盖 {report.stock_count} 只自选股，点击查看详情",
                        type="report",
                        ref_id=report.id,
                    )
                    logger.info(f"用户 {user_id} 复盘报告生成完成，{report.stock_count} 只股票")
                else:
                    logger.warning(f"用户 {user_id} 复盘报告生成失败")

            except Exception as e:
                logger.error(f"生成用户 {user_id} 复盘报告异常: {e}", exc_info=True)
                continue

    finally:
        db.close()

    logger.info("盘后复盘定时任务执行完毕")


def start_scheduler():
    """启动定时任务调度器。"""
    global _scheduler
    if not settings.scheduler_enabled:
        logger.info("定时任务已禁用，跳过启动")
        return

    if _scheduler and _scheduler.running:
        return

    _scheduler = BackgroundScheduler(timezone="Asia/Shanghai")

    # 盘后复盘：周一到周五 15:30
    # 从 settings.daily_report_cron 解析 cron 表达式
    cron_parts = settings.daily_report_cron.strip().split()
    if len(cron_parts) == 5:
        trigger = CronTrigger(
            minute=cron_parts[0],
            hour=cron_parts[1],
            day=cron_parts[2],
            month=cron_parts[3],
            day_of_week=cron_parts[4],
            timezone="Asia/Shanghai",
        )
    else:
        # 默认
        trigger = CronTrigger(
            minute="30", hour="15", day_of_week="mon-fri", timezone="Asia/Shanghai"
        )

    _scheduler.add_job(
        run_daily_report_job,
        trigger=trigger,
        id="daily_report_job",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info(f"定时任务调度器已启动，盘后复盘 Cron: {settings.daily_report_cron}")


def shutdown_scheduler():
    """关闭定时任务调度器。"""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("定时任务调度器已关闭")
```

- [ ] **Step 2: 在 main.py 中集成 scheduler**

在启动事件（preload_data 或 lifespan）中调用 `start_scheduler()`，在关闭事件中调用 `shutdown_scheduler()`。
如果项目用的是 `@app.on_event("startup")`，就加一个 startup 和一个 shutdown 事件处理器。

- [ ] **Step 3: 启动验证 scheduler 正常加载**
```bash
cd backend && source venv/bin/activate && uvicorn app.main:app --port 8000 &
sleep 3
# 查看日志中是否有"定时任务调度器已启动"
kill %1
```
Expected: 启动日志中出现 `定时任务调度器已启动` 字样，无报错。

---

## Phase 5: 前端用户系统

### Task 5.1: 用户 Store + API 封装 + Axios 拦截器

**Files:**
- Create: `frontend/src/store/user.js`
- Create: `frontend/src/api/auth.js`
- Create: `frontend/src/api/http.js`（通用 axios 实例）
- Modify: `frontend/src/api/stock.js`

**Interfaces:**
- Produces: `useUserStore()` (Pinia)，`authApi` 对象，`http` axios 实例（带 token 拦截器 + 401 处理）

- [ ] **Step 1: 创建通用 axios 实例 http.js**

```javascript
// 通用 axios 实例，自动注入 token，401 自动登出
import axios from 'axios'
import { useUserStore } from '@/store/user'

const http = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截器：注入 token
http.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：401 清除登录状态
http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const userStore = useUserStore()
      userStore.logout()
      // 可以在这里触发登录弹窗
      window.dispatchEvent(new CustomEvent('show-login'))
    }
    return Promise.reject(error)
  }
)

export default http
```

- [ ] **Step 2: 创建 auth.js API 封装**

```javascript
// 认证相关 API
import http from './http'

export const authApi = {
  // 注册
  register(username, password) {
    return http.post('/auth/register', { username, password })
  },
  // 登录
  login(username, password) {
    return http.post('/auth/login', { username, password })
  },
  // 获取当前用户
  getMe() {
    return http.get('/auth/me')
  },
}
```

- [ ] **Step 3: 创建 user store**

```javascript
// 用户状态管理
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'

const TOKEN_KEY = 'stock_user_token'
const USER_KEY = 'stock_user_info'

export const useUserStore = defineStore('user', () => {
  // state
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const userInfo = ref(JSON.parse(localStorage.getItem(USER_KEY) || 'null'))

  // getters
  const isLoggedIn = computed(() => !!token.value && !!userInfo.value)
  const username = computed(() => userInfo.value?.username || '')

  // actions
  async function login(username, password) {
    const res = await authApi.login(username, password)
    const { access_token, user } = res.data
    token.value = access_token
    userInfo.value = user
    localStorage.setItem(TOKEN_KEY, access_token)
    localStorage.setItem(USER_KEY, JSON.stringify(user))
    return user
  }

  async function register(username, password) {
    const res = await authApi.register(username, password)
    return res.data
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  async function fetchUserInfo() {
    if (!token.value) return null
    try {
      const res = await authApi.getMe()
      userInfo.value = res.data
      localStorage.setItem(USER_KEY, JSON.stringify(res.data))
      return res.data
    } catch (e) {
      // token 无效，清除
      logout()
      return null
    }
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    username,
    login,
    register,
    logout,
    fetchUserInfo,
  }
})
```

- [ ] **Step 4: 改造 stock.js 使用通用 http 实例**

将 `frontend/src/api/stock.js` 中的 axios 实例替换为从 `http.js` 导入的 `http`（或保持现有 stock API 的导入方式，但底层共用 http 实例）。SSE EventSource 部分也需要在 URL 上加 token 参数或保持现状（复盘 API 不涉及 SSE）。

- [ ] **Step 5: 验证前端构建通过**
```bash
cd frontend && npm run build
```
Expected: 构建成功，无报错。

---

### Task 5.2: 登录/注册弹窗组件

**Files:**
- Create: `frontend/src/components/LoginModal.vue`
- Modify: `frontend/src/App.vue` 或 `Layout.vue`

**Interfaces:**
- Produces: `LoginModal` 组件，通过全局事件 `show-login` 触发显示

- [ ] **Step 1: 创建 LoginModal.vue**

使用 Element Plus 的 `el-dialog` + `el-tabs`（登录/注册切换）+ `el-form`：
- 登录 Tab：用户名 + 密码 + 登录按钮
- 注册 Tab：用户名 + 密码 + 确认密码 + 注册按钮
- 表单校验：用户名 3-50 字符，密码至少 6 位，确认密码一致
- 登录/注册成功后关闭弹窗，emit `success` 事件
- 监听全局 `show-login` 事件自动打开

- [ ] **Step 2: 在 App.vue 中引入登录弹窗**

在 App.vue 中 `<Layout />` 下面添加 `<LoginModal ref="loginModalRef" />`，并在 mounted 时监听 `show-login` 事件。

- [ ] **Step 3: 启动前端验证弹窗可用**
```bash
cd frontend && npm run dev
```
Expected: 页面正常加载，无控制台报错。

---

### Task 5.3: 侧边栏用户区改造

**Files:**
- Modify: `frontend/src/components/Layout.vue`

**Interfaces:**
- Produces: 侧边栏底部显示「登录/注册」按钮（未登录）或「用户名 + 退出菜单」（已登录）

- [ ] **Step 1: 改造侧边栏底部用户区**

- 未登录状态：显示「点击登录」按钮，点击打开登录弹窗
- 已登录状态：显示头像 + 用户名 + 下拉菜单（退出登录）
- 使用 `useUserStore()` 获取登录状态

- [ ] **Step 2: 验证布局正常**

启动前端，验证登录前后侧边栏底部显示正确。

---

## Phase 6: 前端自选股云端同步

### Task 6.1: Watchlist API 封装 + Store 改造

**Files:**
- Create: `frontend/src/api/watchlist.js`
- Modify: `frontend/src/store/index.js`
- Modify: `frontend/src/views/Watchlist.vue`

**Interfaces:**
- Produces: `watchlistApi`；Pinia watchlist store 支持「云端模式」和「本地模式」自动切换

- [ ] **Step 1: 创建 watchlist.js API**

```javascript
// 自选股相关 API
import http from './http'

export const watchlistApi = {
  // 获取所有分组（含股票）
  getGroups() {
    return http.get('/watchlist/groups')
  },
  // 新建分组
  createGroup(name) {
    return http.post('/watchlist/groups', { name })
  },
  // 重命名分组
  updateGroup(id, name) {
    return http.put(`/watchlist/groups/${id}`, { name })
  },
  // 删除分组
  deleteGroup(id) {
    return http.delete(`/watchlist/groups/${id}`)
  },
  // 添加股票
  addItem(groupId, stockCode, stockName, cost = 0, remark = '') {
    return http.post('/watchlist/items', { group_id: groupId, stock_code: stockCode, stock_name: stockName, cost, remark })
  },
  // 更新股票
  updateItem(id, data) {
    return http.put(`/watchlist/items/${id}`, data)
  },
  // 删除股票
  deleteItem(id) {
    return http.delete(`/watchlist/items/${id}`)
  },
  // 批量同步
  sync(groups, replace = false) {
    return http.post('/watchlist/sync', { groups, replace })
  },
}
```

- [ ] **Step 2: 改造 watchlist store**

在 `store/index.js` 中：
- 添加 `cloudMode` 状态（是否使用云端）
- 登录后自动切换到云端模式，从后端拉取数据
- 未登录保持 localStorage 模式（现有逻辑不变）
- 所有操作（增删改）根据模式自动走本地或云端
- 首次登录检测 localStorage 有数据则提示同步

- [ ] **Step 3: 改造 Watchlist.vue**

Watchlist 视图基本保持不变，store 的接口不变（云模式对视图透明）。
但需要添加「首次登录同步提示」的逻辑。

- [ ] **Step 4: 验证前端构建通过**
```bash
cd frontend && npm run build
```
Expected: 构建成功。

---

## Phase 7: 前端复盘报告 + 消息中心

### Task 7.1: 通知铃铛 + 通知 API

**Files:**
- Create: `frontend/src/api/notification.js`
- Create: `frontend/src/components/NotificationBell.vue`
- Modify: `frontend/src/components/Layout.vue`

**Interfaces:**
- Produces: `notificationApi`；`NotificationBell` 组件（铃铛 + 未读红点 + 下拉列表）

- [ ] **Step 1: 创建 notification.js API**

```javascript
// 通知相关 API
import http from './http'

export const notificationApi = {
  // 获取通知列表
  getList(params = {}) {
    return http.get('/notifications', { params })
  },
  // 未读数量
  getUnreadCount() {
    return http.get('/notifications/unread-count')
  },
  // 标记已读
  markAsRead(id) {
    return http.put(`/notifications/${id}/read`)
  },
  // 全部已读
  markAllRead() {
    return http.put('/notifications/read-all')
  },
}
```

- [ ] **Step 2: 创建 NotificationBell.vue 组件**

使用 Element Plus 的 `el-badge` + `el-dropdown`：
- 铃铛图标 + 未读数红点（超过 99 显示 99+）
- 点击铃铛展开下拉列表（最近 10 条）
- 列表项：标题、摘要、时间，未读高亮
- 点击通知项：标记已读 + 跳转到对应页面（report 类型跳复盘详情）
- 底部「全部已读」按钮
- 登录后每 60 秒轮询一次未读数（可选，第一版先做页面加载时获取 + 点击刷新）

- [ ] **Step 3: 在 Layout.vue 中添加铃铛**

在侧边栏顶部或主内容区右上角添加 `NotificationBell` 组件。

- [ ] **Step 4: 验证构建通过**
```bash
cd frontend && npm run build
```
Expected: 构建成功。

---

### Task 7.2: 复盘报告列表页 + 详情页

**Files:**
- Create: `frontend/src/api/report.js`
- Create: `frontend/src/views/Reports.vue`
- Create: `frontend/src/views/ReportDetail.vue`
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/components/Layout.vue`（导航项）

**Interfaces:**
- Produces: 复盘报告列表页 `/reports` + 详情页 `/reports/:id`；侧边栏导航项

- [ ] **Step 1: 创建 report.js API**

```javascript
// 复盘报告相关 API
import http from './http'

export const reportApi = {
  // 报告列表
  getList(params = {}) {
    return http.get('/reports', { params })
  },
  // 报告详情
  getDetail(id) {
    return http.get(`/reports/${id}`)
  },
  // 手动生成今日报告
  generateToday() {
    return http.post('/reports/generate')
  },
}
```

- [ ] **Step 2: 创建 Reports.vue（列表页）**

页面结构：
- 页面标题「复盘报告」+ 「手动生成今日报告」按钮
- 报告卡片列表（或表格），按日期倒序
- 每条显示：日期、状态、覆盖股票数、市场总览摘要
- 点击跳转到详情页
- 分页

- [ ] **Step 3: 创建 ReportDetail.vue（详情页）**

页面结构：
- 返回按钮 + 日期标题
- 市场总览卡片（AI 生成的市场点评）
- 关注重点卡片（3-5 只股票，每只有理由）
- 个股分析列表：每只股票一个折叠面板，显示涨跌幅 + 一句话摘要，展开看完整分析
- 风险提示卡片

- [ ] **Step 4: 添加路由 + 导航**

在 `router/index.js` 中添加 `/reports` 和 `/reports/:id` 路由。
在 `Layout.vue` 侧边栏菜单中添加「复盘报告」导航项。
路由守卫：复盘页需登录，未登录跳登录弹窗。

- [ ] **Step 5: 验证构建通过**
```bash
cd frontend && npm run build
```
Expected: 构建成功。

---

## Phase 8: 集成测试 + 文档更新

### Task 8.1: 端到端测试 + 边界情况验证

- [ ] **Step 1: 完整注册登录流程测试**
  - 注册新用户 → 登录 → 访问 /me → 退出 → 再次登录
  - 错误密码 → 401
  - 重复用户名 → 400

- [ ] **Step 2: 自选股云端同步测试**
  - 未登录时添加几支自选股到 localStorage
  - 登录 → 提示同步 → 确认同步 → 验证数据在云端
  - 新增/删除/修改成本 → 刷新页面 → 数据保持
  - 退出登录 → 回到本地模式（localStorage 数据还在）

- [ ] **Step 3: 复盘报告手动生成测试**
  - 添加几支自选股
  - 手动触发生成
  - 验证报告生成完成、有内容、通知到达
  - 查看列表页和详情页

- [ ] **Step 4: 消息中心测试**
  - 生成报告后铃铛显示未读数
  - 点击通知跳转详情页
  - 标记已读/全部已读
  - 未登录时铃铛不显示

- [ ] **Step 5: 定时任务测试（可选）**
  - 临时修改 cron 为 1 分钟后，验证能自动触发

---

### Task 8.2: 更新文档

**Files:**
- Modify: `stock-analyzer/README.md`
- Modify: `stock-analyzer/PROGRESS.md`

- [ ] **Step 1: 更新 PROGRESS.md**

在「已完成」中添加新功能，更新文件结构，更新启动说明。

- [ ] **Step 2: 更新 README.md**

添加用户系统、自选股同步、盘后复盘的功能说明。

---

## 附录：任务依赖图

```
Phase 1: 数据库基础设施
  └─ Task 1.1 依赖+配置
  └─ Task 1.2 数据库初始化

Phase 2: 用户系统（后端）
  └─ Task 2.1 User Model + Schema
  └─ Task 2.2 Auth Service
  └─ Task 2.3 Auth API

Phase 3: 自选股持久化（后端）
  └─ Task 3.1 Watchlist Model + Schema
  └─ Task 3.2 Watchlist Service + API

Phase 4: 盘后复盘 + 消息中心（后端）
  └─ Task 4.1 Report + Notification Model + Schema
  └─ Task 4.2 Report Service
  └─ Task 4.3 AI 分析扩展
  └─ Task 4.4 Notification Service + API
  └─ Task 4.5 Report API
  └─ Task 4.6 APScheduler 定时任务

Phase 5: 前端用户系统
  └─ Task 5.1 用户 Store + API + 拦截器
  └─ Task 5.2 登录/注册弹窗
  └─ Task 5.3 侧边栏用户区

Phase 6: 前端自选股云端同步
  └─ Task 6.1 Watchlist API + Store 改造

Phase 7: 前端复盘报告 + 消息中心
  └─ Task 7.1 通知铃铛 + API
  └─ Task 7.2 复盘报告页

Phase 8: 集成测试 + 文档
  └─ Task 8.1 端到端测试
  └─ Task 8.2 文档更新
```
