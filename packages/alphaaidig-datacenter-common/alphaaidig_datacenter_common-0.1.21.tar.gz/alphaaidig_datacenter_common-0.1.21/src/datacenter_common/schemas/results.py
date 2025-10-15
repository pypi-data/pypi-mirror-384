"""
通用结果模型
用于API服务和客户端共享的结果类型定义
"""
from typing import Dict, Any, List
from pydantic import BaseModel
from enum import Enum


class ResultType(str, Enum):
    """结果类型枚举"""
    TABLE = "table"        # 表格数据（最常用，fields + items）
    PAGE = "page"          # 分页数据（table + pagination）
    DICT = "dict"          # 键值对数据（统计数据等）
    SINGLE = "single"      # 单条记录


class BaseResult(BaseModel):
    """基础结果模型"""
    success: bool = True
    message: str = "success"
    result_type: ResultType


class TableResult(BaseResult):
    """表格结果模型 - 用于列表数据"""
    result_type: ResultType = ResultType.TABLE
    fields: List[str] = []
    items: List[Dict[str, Any]] = []


class PageResult(TableResult):
    """分页结果模型 - 用于分页列表数据"""
    result_type: ResultType = ResultType.PAGE
    current_page: int = 1
    page_size: int = 20
    total_count: int = 0
    total_pages: int = 0


class DictResult(BaseResult):
    """字典结果模型 - 用于统计数据、配置信息等"""
    result_type: ResultType = ResultType.DICT
    data: Dict[str, Any] = {}


class SingleResult(BaseResult):
    """单条记录结果模型 - 用于详细数据"""
    result_type: ResultType = ResultType.SINGLE
    data: Dict[str, Any] = {}