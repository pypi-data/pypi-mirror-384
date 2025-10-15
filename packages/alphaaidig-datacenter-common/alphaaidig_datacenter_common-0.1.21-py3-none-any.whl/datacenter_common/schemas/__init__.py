"""
数据中心通用schemas模块
"""
from .base import BaseResponse, PaginatedResponse, PaginationInfo
from .results import ResultType, BaseResult, TableResult, PageResult, DictResult, SingleResult
from .a_stock import AStock
from .hk_stock import HKStock
from .index_basic import IndexBasic
from .index_company import IndexCompany
from .margin_account import MarginAccount
from .margin_analysis import MarginAnalysis
from .margin_detail import MarginDetail

from .hs_industry import HSIndustry, HSIndustryCategory
from .hs_industry_company import HSIndustryCompany
from .sw_industry import SWIndustry
from .sw_industry_company import SWIndustryCompany

__all__ = [
    "BaseResponse",
    "PaginatedResponse",
    "PaginationInfo",
    "ResultType",
    "BaseResult",
    "TableResult",
    "PageResult",
    "DictResult",
    "SingleResult",
    "AStock",
    "HKStock",
    "IndexBasic",
    "IndexCompany",
    "MarginAccount",
    "MarginAnalysis",
    "MarginDetail",

    "HSIndustry",
    "HSIndustryCategory",
    "HSIndustryCompany",
    "SWIndustry",
    "SWIndustryCompany",
]