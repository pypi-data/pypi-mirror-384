"""
申万行业相关的Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import Optional

class SWIndustryBase(BaseModel):
    industry_code: str = Field(..., description="行业代码")
    level1_industry: Optional[str] = None
    level2_industry: Optional[str] = None
    level3_industry: Optional[str] = None
    level1_industry_code: Optional[str] = None
    level2_industry_code: Optional[str] = None
    level3_industry_code: Optional[str] = None
    level1_index_code: Optional[str] = None
    level2_index_code: Optional[str] = None
    level3_index_code: Optional[str] = None

class SWIndustry(SWIndustryBase):
    id: int
    index_code: Optional[str] = None

    class Config:
        from_attributes = True

# 一级行业Schema
class SWIndustryLevel1(BaseModel):
    industry_code: str = Field(..., description="一级行业代码")
    index_code: Optional[str] = Field(None, description="一级行业指数代码")
    name: str = Field(..., description="一级行业名称")

# 二级行业Schema
class SWIndustryLevel2(BaseModel):
    industry_code: str = Field(..., description="二级行业代码")
    index_code: Optional[str] = Field(None, description="二级行业指数代码")
    name: str = Field(..., description="二级行业名称")
    level1_industry_code: str = Field(..., description="所属一级行业代码")
    level1_index_code: Optional[str] = Field(None, description="所属一级行业指数代码")
    level1_name: str = Field(..., description="所属一级行业名称")

# 三级行业Schema
class SWIndustryLevel3(BaseModel):
    industry_code: str = Field(..., description="三级行业代码")
    index_code: Optional[str] = Field(None, description="三级行业指数代码")
    name: str = Field(..., description="三级行业名称")
    level1_industry_code: str = Field(..., description="所属一级行业代码")
    level1_index_code: Optional[str] = Field(None, description="所属一级行业指数代码")
    level1_name: str = Field(..., description="所属一级行业名称")
    level2_industry_code: str = Field(..., description="所属二级行业代码")
    level2_index_code: Optional[str] = Field(None, description="所属二级行业指数代码")
    level2_name: str = Field(..., description="所属二级行业名称")