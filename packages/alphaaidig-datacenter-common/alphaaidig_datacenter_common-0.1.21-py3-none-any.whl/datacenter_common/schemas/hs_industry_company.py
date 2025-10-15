"""
恒生行业公司数据模型
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class HSIndustryCompanyBase(BaseModel):
    """恒生行业公司基础模型"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: Optional[str] = Field(None, description="股票名称")
    level1_industry_code: Optional[str] = Field(None, description="一级行业代码")
    level2_industry_code: Optional[str] = Field(None, description="二级行业代码")
    level1_industry_name: Optional[str] = Field(None, description="一级行业名称")
    level2_industry_name: Optional[str] = Field(None, description="二级行业名称")
    entry_date: Optional[datetime] = Field(None, description="纳入日期")
    
    class Config:
        from_attributes = True


class HSIndustryCompany(HSIndustryCompanyBase):
    """恒生行业公司完整模型"""
    id: int = Field(..., description="主键ID")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")