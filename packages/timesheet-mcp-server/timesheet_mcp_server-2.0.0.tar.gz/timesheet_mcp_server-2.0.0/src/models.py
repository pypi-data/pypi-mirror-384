"""数据模型定义."""
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class TimeEntryInput(BaseModel):
    """工时记录输入模型."""

    project_id: int = Field(..., gt=0, description="项目ID")
    work_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="工作日期 (YYYY-MM-DD)")
    hours: float = Field(..., gt=0, le=24, description="工时数")
    work_content: str = Field(..., min_length=1, max_length=500, description="工作内容描述")
    remarks: str = Field(default="", max_length=200, description="备注")

    @field_validator("work_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        """验证日期格式."""
        try:
            date.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError("日期格式无效，应为 YYYY-MM-DD")


class TimeEntryUpdate(BaseModel):
    """工时记录更新模型."""

    project_id: Optional[int] = Field(None, gt=0, description="项目ID")
    work_date: Optional[str] = Field(
        None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="工作日期 (YYYY-MM-DD)"
    )
    hours: Optional[float] = Field(None, gt=0, le=24, description="工时数")
    work_content: Optional[str] = Field(None, min_length=1, max_length=500, description="工作内容描述")
    remarks: Optional[str] = Field(None, max_length=200, description="备注")

    @field_validator("work_date")
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        """验证日期格式."""
        if v is None:
            return v
        try:
            date.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError("日期格式无效，应为 YYYY-MM-DD")


class APIResponse(BaseModel):
    """API 响应基础模型."""

    success: bool = Field(description="请求是否成功")
    message: Optional[str] = Field(None, description="响应消息")
    data: Optional[dict] = Field(None, description="响应数据")


class ErrorResponse(BaseModel):
    """错误响应模型."""

    success: bool = Field(default=False, description="请求失败")
    error: str = Field(description="错误信息")
    details: Optional[str] = Field(None, description="错误详情")
