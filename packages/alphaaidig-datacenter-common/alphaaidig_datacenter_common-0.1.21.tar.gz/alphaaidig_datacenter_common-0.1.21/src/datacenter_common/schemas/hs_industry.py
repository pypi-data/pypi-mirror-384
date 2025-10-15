"""
恒生行业相关的Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class HSIndustryBase(BaseModel):
    level1_industry_code: str = Field(..., description="一级行业代码")
    level1_industry_name: str = Field(..., description="一级行业名称")
    level2_industry_code: Optional[str] = None
    level2_industry_name: Optional[str] = None
    level3_industry_code: Optional[str] = None
    level3_industry_name: Optional[str] = None
    description: Optional[str] = None

class HSIndustry(HSIndustryBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# 为了兼容性，添加别名
HSIndustryCategory = HSIndustry