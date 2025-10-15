"""
融资融券交易明细相关的Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MarginDetailBase(BaseModel):
    trade_date: str = Field(..., description="交易日期（格式：YYYYMMDD）")
    stock_code: str = Field(..., description="股票代码")
    name: Optional[str] = Field(None, description="股票名称")
    rzye: Optional[int] = Field(None, description="融资余额(分)")
    rqye: Optional[int] = Field(None, description="融券余额(分)")
    rzmre: Optional[int] = Field(None, description="融资买入额(分)")
    rqyl: Optional[int] = Field(None, description="融券余量（股）")
    rzche: Optional[int] = Field(None, description="融资偿还额(分)")
    rqchl: Optional[int] = Field(None, description="融券偿还量(股)")
    rqmcl: Optional[int] = Field(None, description="融券卖出量(股,份,手)")
    rzrqye: Optional[int] = Field(None, description="融资融券余额(分)")
    rzjme: Optional[int] = Field(None, description="当日融资净买入额(分)")
    rqjml: Optional[int] = Field(None, description="融券净买入量(股)")

class MarginDetail(MarginDetailBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True