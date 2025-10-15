"""
申万行业公司相关的数据传输对象（DTO）
"""
from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field

from .base import PaginationInfoDTO, StandardResponseDTO, StandardListResponseDTO, TimestampFields, IdFields


class SWIndustryCompanyItem(BaseModel, TimestampFields, IdFields):
    """申万行业公司项"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    industry_code: str = Field(..., description="行业代码")
    level1_industry: str = Field(..., description="一级行业名称")
    level2_industry: Optional[str] = Field(None, description="二级行业名称")
    level3_industry: Optional[str] = Field(None, description="三级行业名称")
    level1_industry_code: str = Field(..., description="一级行业代码")
    level2_industry_code: Optional[str] = Field(None, description="二级行业代码")
    level3_industry_code: Optional[str] = Field(None, description="三级行业代码")
    entry_date: Optional[datetime] = Field(None, description="纳入日期")


class SWIndustryCompanyResponse(StandardResponseDTO):
    """申万行业公司响应"""
    
    @property
    def item(self) -> Optional[SWIndustryCompanyItem]:
        """获取申万行业公司项"""
        if isinstance(self.data, dict):
            return SWIndustryCompanyItem(**self.data)
        elif isinstance(self.data, SWIndustryCompanyItem):
            return self.data
        return None


class SWIndustryCompanyListResponse(StandardListResponseDTO):
    """申万行业公司列表响应"""
    
    def __init__(self, **data):
        """初始化方法，处理没有data字段的情况"""
        # 如果传入的数据没有data字段，但有items或pagination字段，则将整个数据作为data
        if "data" not in data and ("items" in data or "pagination" in data):
            super().__init__(status=data.get("status", "success"), data=data)
        else:
            super().__init__(**data)
    
    @property
    def items(self) -> List[SWIndustryCompanyItem]:
        """获取申万行业公司项列表"""
        if isinstance(self.data, dict) and "items" in self.data:
            return [SWIndustryCompanyItem(**item) if isinstance(item, dict) else item for item in self.data["items"]]
        elif isinstance(self.data, list):
            return [SWIndustryCompanyItem(**item) if isinstance(item, dict) else item for item in self.data]
        return []
    
    @property
    def pagination(self) -> Optional[PaginationInfoDTO]:
        """获取分页信息"""
        if isinstance(self.data, dict) and "pagination" in self.data and self.data["pagination"]:
            return PaginationInfoDTO(**self.data["pagination"])
        return None
    
    @property
    def total(self) -> int:
        """获取总记录数"""
        if isinstance(self.data, dict) and "total" in self.data:
            return self.data["total"]
        if self.pagination:
            return self.pagination.total
        return len(self.items)


class IndustryCompanyCountItem(BaseModel):
    """行业公司数量统计项"""
    industry_code: str = Field(..., description="行业代码")
    industry_name: str = Field(..., description="行业名称")
    company_count: int = Field(..., description="公司数量")


class IndustryCompanyCountResponse(StandardListResponseDTO):
    """行业公司数量统计响应"""
    
    def __init__(self, **data):
        """初始化方法，处理没有data字段的情况"""
        # 如果传入的数据没有data字段，但有items字段，则将整个数据作为data
        if "data" not in data and "items" in data:
            super().__init__(status=data.get("status", "success"), data=data)
        else:
            super().__init__(**data)
    
    @property
    def items(self) -> List[IndustryCompanyCountItem]:
        """获取行业公司数量统计项列表"""
        if isinstance(self.data, dict) and "items" in self.data:
            return [IndustryCompanyCountItem(**item) if isinstance(item, dict) else item for item in self.data["items"]]
        elif isinstance(self.data, list):
            return [IndustryCompanyCountItem(**item) if isinstance(item, dict) else item for item in self.data]
        return []