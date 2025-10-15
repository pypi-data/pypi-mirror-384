"""
融资融券分析结果相关的Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MarginAnalysisResultBase(BaseModel):
    trade_date: str = Field(..., description="交易日期（格式：YYYYMMDD）")
    analysis_type: str = Field(..., description="分析类型: index/industry")
    target_code: str = Field(..., description="目标代码(指数代码/行业代码)")
    target_name: Optional[str] = Field(None, description="目标名称")
    company_count: Optional[int] = Field(None, description="包含公司数量")
    trade_company_count: Optional[int] = Field(None, description="有交易公司数量")
    rz_net_inflow_count: Optional[int] = Field(None, description="融资净流入公司数")
    rz_net_outflow_count: Optional[int] = Field(None, description="融资净流出公司数")
    rq_net_sell_count: Optional[int] = Field(None, description="融券净卖出公司数")
    
    # 融资融券聚合字段
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

class MarginAnalysisResult(MarginAnalysisResultBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 别名定义，以便与导入名称保持一致
MarginAnalysis = MarginAnalysisResult