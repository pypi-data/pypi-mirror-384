"""配置管理模块."""
import os
from typing import Optional

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Settings:
    """应用配置类."""

    # API 配置
    API_BASE_URL: str = os.getenv("TIMESHEET_API_BASE_URL", "http://127.0.0.1:8080/api")
    API_TOKEN: str = os.getenv("TIMESHEET_API_TOKEN", "")

    # MCP 服务器配置
    MCP_TRANSPORT: str = os.getenv("MCP_TRANSPORT", "stdio")
    MCP_LOG_LEVEL: str = os.getenv("MCP_LOG_LEVEL", "INFO")

    # 功能开关
    ENABLE_CACHE: bool = os.getenv("ENABLE_CACHE", "true").lower() == "true"
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))
    ENABLE_RATE_LIMIT: bool = os.getenv("ENABLE_RATE_LIMIT", "true").lower() == "true"
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

    # 开发配置
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    @classmethod
    def validate(cls) -> None:
        """验证配置."""
        if not cls.API_BASE_URL:
            raise ValueError("TIMESHEET_API_BASE_URL is required")
        if not cls.API_TOKEN:
            raise ValueError("TIMESHEET_API_TOKEN is required")

    @classmethod
    def get_headers(cls) -> dict[str, str]:
        """获取 API 请求头."""
        return {
            "Authorization": f"Bearer {cls.API_TOKEN}",
            "Content-Type": "application/json",
        }


# 创建全局配置实例
settings = Settings()
