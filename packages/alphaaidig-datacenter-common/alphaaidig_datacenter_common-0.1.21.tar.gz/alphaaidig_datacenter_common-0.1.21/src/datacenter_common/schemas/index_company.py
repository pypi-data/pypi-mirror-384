"""
指数成分公司相关的Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class IndexCompanyBase(BaseModel):
    index_code: str = Field(..., description="指数代码")
    con_code: str = Field(..., description="成分代码")
    weight: Optional[float] = Field(None, description="权重")

class IndexCompany(IndexCompanyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True