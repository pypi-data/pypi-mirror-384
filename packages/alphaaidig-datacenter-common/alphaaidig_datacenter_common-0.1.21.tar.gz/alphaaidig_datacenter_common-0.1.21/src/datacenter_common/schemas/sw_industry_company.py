"""
申万行业公司数据模式
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SWIndustryCompanyBase(BaseModel):
    """申万行业公司基础模式"""
    stock_code: str
    stock_name: str
    industry_code: str
    level1_industry: str
    level2_industry: Optional[str] = None
    level3_industry: Optional[str] = None
    level1_industry_code: str
    level2_industry_code: Optional[str] = None
    level3_industry_code: Optional[str] = None
    entry_date: Optional[datetime] = None
    
class SWIndustryCompany(SWIndustryCompanyBase):
    """申万行业公司完整模式"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True