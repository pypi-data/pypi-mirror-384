"""
A股相关的Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AStockBase(BaseModel):
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    exchange: str = Field(..., description="交易所(SH/SZ/BJ)")
    list_status: Optional[str] = Field(None, description="上市状态(L上市/D退市/P暂停上市)")
    list_date: Optional[datetime] = Field(None, description="上市日期")
    curr_type: Optional[str] = Field(None, description="交易货币(CNY)")
    market: Optional[str] = Field(None, description="市场类型(主板/创业板/科创板/北交所)")
    ric_code: Optional[str] = Field(None, description="路透代码")

class AStock(AStockBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True