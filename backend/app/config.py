"""
应用配置模块
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 锚定到 backend/ 目录，避免因启动 cwd 不同而写出多个 stock_analyzer.db
BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE_URL = f"sqlite:///{BACKEND_DIR / 'stock_analyzer.db'}"


class Settings:
    # 火山引擎 Coding Plan (Claude API 兼容)
    # 支持环境变量：ARK_API_KEY / ANTHROPIC_AUTH_TOKEN
    # ARK_BASE_URL / ANTHROPIC_BASE_URL
    ARK_API_KEY: str = os.getenv("ARK_API_KEY", os.getenv("ANTHROPIC_AUTH_TOKEN", ""))
    ARK_MODEL: str = os.getenv("ARK_MODEL", os.getenv("ARK_MODEL_ID", "claude-3-5-sonnet-20241022"))
    ARK_BASE_URL: str = os.getenv("ARK_BASE_URL", os.getenv("ANTHROPIC_BASE_URL", "https://ark.cn-beijing.volces.com/api/coding/v3"))

    # 服务配置
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "52764"))

    # CORS 允许的前端地址
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # 数据库配置
    database_url: str = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

    # JWT 配置
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_access_token_expire_hours: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_HOURS", "24"))

    # 定时任务配置
    scheduler_enabled: bool = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
    daily_report_cron: str = os.getenv("DAILY_REPORT_CRON", "30 15 * * 1-5")

    @property
    def ai_available(self) -> bool:
        """AI 服务是否可用"""
        return bool(self.ARK_API_KEY and self.ARK_MODEL)


settings = Settings()
