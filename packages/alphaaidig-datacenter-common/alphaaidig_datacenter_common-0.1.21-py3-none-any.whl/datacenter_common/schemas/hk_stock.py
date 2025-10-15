"""
港股相关的Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date

class HKStockBase(BaseModel):
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    ric_code: Optional[str] = Field(None, description="RIC代码")
    currency: Optional[str] = Field(None, description="货币(HKD/USD/CNY)")
    is_suspended: Optional[bool] = Field(False, description="是否停牌")
    list_date: Optional[date] = Field(None, description="上市日期")
    list_status: Optional[str] = Field(None, description="上市状态(L上市/P停牌/D退市)")
    fullname: Optional[str] = Field(None, description="公司全称")
    market: Optional[str] = Field(None, description="市场类型")

class HKStock(HKStockBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True