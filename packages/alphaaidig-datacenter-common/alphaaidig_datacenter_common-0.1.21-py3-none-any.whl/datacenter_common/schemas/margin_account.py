"""
融资融券账户统计相关的Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MarginAccountBase(BaseModel):
    trade_date: str = Field(..., description="交易日期（格式：YYYY-MM-DD）")
    financing_balance: Optional[int] = Field(None, description="融资余额(分)")
    margin_balance: Optional[int] = Field(None, description="融券余额(分)")
    financing_purchase: Optional[int] = Field(None, description="融资买入额(分)")
    margin_sell: Optional[int] = Field(None, description="融券卖出额(分)")
    securities_company_count: Optional[int] = Field(None, description="证券公司数量(家)")
    business_department_count: Optional[int] = Field(None, description="营业部数量(个)")
    individual_investor_count: Optional[int] = Field(None, description="个人投资者数量(户)")
    institutional_investor_count: Optional[int] = Field(None, description="机构投资者数量(户)")
    trading_investor_count: Optional[int] = Field(None, description="参与交易的投资者数量(户)")
    indebted_investor_count: Optional[int] = Field(None, description="有融资融券负债的投资者数量(户)")
    collateral_value: Optional[int] = Field(None, description="担保物总价值(分)")
    maintenance_ratio: Optional[float] = Field(None, description="平均维持担保比例(%)")

class MarginAccount(MarginAccountBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True