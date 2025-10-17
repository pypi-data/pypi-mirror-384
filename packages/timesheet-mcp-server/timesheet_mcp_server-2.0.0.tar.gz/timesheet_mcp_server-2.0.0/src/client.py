"""API 客户端模块."""
from typing import Any, Optional

import httpx

from config.settings import settings


class TimesheetAPIClient:
    """工时系统 API 客户端."""

    def __init__(self) -> None:
        """初始化客户端."""
        self.base_url = settings.API_BASE_URL
        self.headers = settings.get_headers()

    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """发起 HTTP 请求.

        Args:
            method: HTTP 方法 (GET, POST, PUT, DELETE, PATCH)
            endpoint: API 端点路径
            params: URL 查询参数
            data: 请求体数据

        Returns:
            API 响应数据

        Raises:
            httpx.HTTPStatusError: HTTP 错误
            Exception: 其他错误
        """
        url = f"{self.base_url}{endpoint}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    headers=self.headers,
                    params=params,
                    json=data,
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                error_detail = f"HTTP {e.response.status_code}"
                try:
                    error_body = e.response.json()
                    if "message" in error_body:
                        error_detail = f"{error_detail}: {error_body['message']}"
                except Exception:
                    pass
                raise Exception(f"API 请求失败: {error_detail}") from e

            except httpx.RequestError as e:
                raise Exception(f"网络请求错误: {str(e)}") from e

            except Exception as e:
                raise Exception(f"未知错误: {str(e)}") from e

    async def get(
        self, endpoint: str, params: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """GET 请求."""
        return await self.request("GET", endpoint, params=params)

    async def post(
        self,
        endpoint: str,
        data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """POST 请求."""
        return await self.request("POST", endpoint, params=params, data=data)

    async def put(
        self,
        endpoint: str,
        data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """PUT 请求."""
        return await self.request("PUT", endpoint, params=params, data=data)

    async def delete(
        self, endpoint: str, params: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """DELETE 请求."""
        return await self.request("DELETE", endpoint, params=params)

    async def patch(
        self,
        endpoint: str,
        data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """PATCH 请求."""
        return await self.request("PATCH", endpoint, params=params, data=data)


# 创建全局客户端实例
api_client = TimesheetAPIClient()
