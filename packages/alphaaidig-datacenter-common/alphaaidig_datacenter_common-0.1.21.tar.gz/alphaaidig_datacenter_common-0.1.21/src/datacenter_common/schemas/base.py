"""
基础Pydantic模型
"""
from typing import Any, Generic, TypeVar, List, Optional
from pydantic import BaseModel, Field

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    total: int
    page: int
    size: int
    items: List[T]

class BaseResponse(BaseModel):
    """基础响应模型"""
    status: str = "success"
    message: Optional[str] = None
    data: Optional[dict] = None

class PaginationInfo(BaseModel):
    """分页信息响应模型"""
    total: int
    page: int
    page_size: int
    total_pages: int

class StandardListResponse(BaseModel):
    """标准列表响应模型，类似Java中的Result<T>"""
    status: str = "success"
    data: dict

class StandardResponse(BaseModel):
    """标准通用响应模型"""
    status: str = "success"
    data: Any

class PydanticPaginationResult(BaseModel, Generic[T]):
    """支持Pydantic模型的分页查询结果"""
    items: List[T] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 10
    total_pages: int = 0