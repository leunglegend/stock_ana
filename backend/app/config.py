"""
应用配置模块
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # 火山引擎 Coding Plan (Claude API 兼容)
    # 支持环境变量：ARK_API_KEY / ANTHROPIC_AUTH_TOKEN
    # ARK_BASE_URL / ANTHROPIC_BASE_URL
    ARK_API_KEY: str = os.getenv("ARK_API_KEY", os.getenv("ANTHROPIC_AUTH_TOKEN", ""))
    ARK_MODEL: str = os.getenv("ARK_MODEL", os.getenv("ARK_MODEL_ID", "claude-3-5-sonnet-20241022"))
    ARK_BASE_URL: str = os.getenv("ARK_BASE_URL", os.getenv("ANTHROPIC_BASE_URL", "https://ark.cn-beijing.volces.com/api/coding/v3"))

    # 服务配置
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # CORS 允许的前端地址
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @property
    def ai_available(self) -> bool:
        """AI 服务是否可用"""
        return bool(self.ARK_API_KEY and self.ARK_MODEL)


settings = Settings()
