"""
MCPStore Common Response Models

统一的响应模型导入中心。
"""

# ==================== 核心响应模型 ====================
from .response import (
    APIResponse,
    ErrorDetail,
    ResponseMeta,
    Pagination
)

# 响应构造器
from .response_builder import (
    ResponseBuilder,
    TimedResponseBuilder
)

# 响应装饰器
from .response_decorators import (
    timed_response,
    paginated,
    handle_errors,
    api_endpoint
)

# 错误码枚举
from .error_codes import ErrorCode

# ==================== 兼容导出（部分旧模型） ====================
from typing import Optional, Any, List, Dict, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T')

class ListResponse(BaseModel, Generic[T]):
    """List response model"""
    success: bool = Field(..., description="Whether operation was successful")
    message: Optional[str] = Field(None, description="Response message")
    items: List[T] = Field(..., description="Data item list")
    total: int = Field(..., description="Total count")

class DataResponse(BaseModel, Generic[T]):
    """Data response model"""
    success: bool = Field(..., description="Whether operation was successful")
    message: Optional[str] = Field(None, description="Response message")
    data: T = Field(..., description="Response data")

class RegistrationResponse(BaseModel):
    """Service registration response"""
    success: bool = Field(..., description="Whether operation was successful")
    message: str = Field(..., description="Response message")
    service_name: Optional[str] = Field(None, description="Registered service name")

class ExecutionResponse(BaseModel):
    """Tool execution response"""
    success: bool = Field(..., description="Whether operation was successful")
    message: Optional[str] = Field(None, description="Response message")
    result: Optional[Any] = Field(None, description="Execution result")
    error: Optional[str] = Field(None, description="Error message")

class ConfigResponse(BaseModel):
    """Configuration operation response"""
    success: bool = Field(..., description="Whether operation was successful")
    message: str = Field(..., description="Response message")
    config: Optional[Dict[str, Any]] = Field(None, description="Configuration data")

class HealthResponse(BaseModel):
    """Health check response"""
    success: bool = Field(..., description="Whether operation was successful")
    status: str = Field(..., description="Health status")
    services: Optional[Dict[str, str]] = Field(None, description="Service status mapping")
