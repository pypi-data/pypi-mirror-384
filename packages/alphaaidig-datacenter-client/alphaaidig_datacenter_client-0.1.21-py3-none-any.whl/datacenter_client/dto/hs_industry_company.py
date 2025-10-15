"""
恒生行业公司相关的数据传输对象（DTO）
"""
from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field

from .base import PaginationInfoDTO, StandardResponseDTO, StandardListResponseDTO, TimestampFields, IdFields


class HSIndustryCompanyItem(BaseModel):
    """恒生行业公司项"""
    id: int = Field(..., description="主键ID")
    stock_code: str = Field(..., description="股票代码")
    stock_name: Optional[str] = Field(None, description="股票名称")
    level1_industry_code: Optional[str] = Field(None, description="一级行业代码")
    level1_industry_name: Optional[str] = Field(None, description="一级行业名称")
    level2_industry_code: Optional[str] = Field(None, description="二级行业代码")
    level2_industry_name: Optional[str] = Field(None, description="二级行业名称")
    entry_date: Optional[datetime] = Field(None, description="纳入日期")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class HSIndustryCompanyListResponse(StandardListResponseDTO):
    """恒生行业公司列表响应"""
    
    def __init__(self, **data):
        """初始化方法，处理没有data字段的情况"""
        # 如果传入的数据没有data字段，但有items或total字段，则将整个数据作为data
        if "data" not in data and ("items" in data or "total" in data):
            super().__init__(status=data.get("status", "success"), data=data)
        else:
            super().__init__(**data)
    
    @property
    def items(self) -> List[HSIndustryCompanyItem]:
        """获取恒生行业公司项列表"""
        if isinstance(self.data, dict) and "items" in self.data:
            return [HSIndustryCompanyItem(**item) if isinstance(item, dict) else item for item in self.data["items"]]
        elif isinstance(self.data, list):
            # 如果data直接是列表
            return [HSIndustryCompanyItem(**item) if isinstance(item, dict) else item for item in self.data]
        return []
    
    @property
    def pagination(self) -> Optional[PaginationInfoDTO]:
        """获取分页信息"""
        if isinstance(self.data, dict) and "pagination" in self.data and self.data["pagination"]:
            return PaginationInfoDTO(**self.data["pagination"])
        # 如果data中包含分页信息，创建分页对象
        if isinstance(self.data, dict) and "total" in self.data and "page" in self.data and "page_size" in self.data:
            return PaginationInfoDTO(
                total=self.data["total"],
                page=self.data["page"],
                page_size=self.data["page_size"],
                total_pages=(self.data["total"] + self.data["page_size"] - 1) // self.data["page_size"]
            )
        return None
    
    @property
    def page(self) -> int:
        """获取当前页码"""
        if self.pagination:
            return self.pagination.page
        return 1
    
    @property
    def page_size(self) -> int:
        """获取每页大小"""
        if self.pagination:
            return self.pagination.page_size
        return len(self.items)
    
    @property
    def total(self) -> int:
        """获取总记录数"""
        if isinstance(self.data, dict) and "total" in self.data:
            return self.data["total"]
        if self.pagination:
            return self.pagination.total
        return len(self.items)


class HSIndustryCompanyDetailResponse(StandardResponseDTO):
    """恒生行业公司详情响应"""
    
    def __init__(self, **data):
        """初始化方法，处理没有data字段的情况"""
        # 如果传入的数据没有data字段，则将整个数据作为data
        if "data" not in data:
            super().__init__(status=data.get("status", "success"), data=data)
        else:
            super().__init__(**data)
    
    @property
    def company(self) -> HSIndustryCompanyItem:
        """获取恒生行业公司项"""
        if isinstance(self.data, dict) and "item" in self.data:
            return HSIndustryCompanyItem(**self.data["item"])
        # 如果data不是字典或没有item字段，返回空对象
        return HSIndustryCompanyItem.model_construct()


class HSIndustryCompanyByIndustryResponse(StandardListResponseDTO):
    """按行业查询恒生行业公司响应"""
    
    def __init__(self, **data):
        """初始化方法，处理没有data字段的情况"""
        # 如果传入的数据没有data字段，但有items或total字段，则将整个数据作为data
        if "data" not in data and ("items" in data or "total" in data):
            super().__init__(status=data.get("status", "success"), data=data)
        else:
            super().__init__(**data)
    
    @property
    def items(self) -> List[HSIndustryCompanyItem]:
        """获取恒生行业公司项列表"""
        if isinstance(self.data, dict) and "items" in self.data:
            return [HSIndustryCompanyItem(**item) if isinstance(item, dict) else item for item in self.data["items"]]
        elif isinstance(self.data, list):
            # 如果data直接是列表
            return [HSIndustryCompanyItem(**item) if isinstance(item, dict) else item for item in self.data]
        return []
    
    @property
    def pagination(self) -> Optional[PaginationInfoDTO]:
        """获取分页信息"""
        if isinstance(self.data, dict) and "pagination" in self.data and self.data["pagination"]:
            return PaginationInfoDTO(**self.data["pagination"])
        # 如果data中包含分页信息，创建分页对象
        if isinstance(self.data, dict) and "total" in self.data and "page" in self.data and "page_size" in self.data:
            return PaginationInfoDTO(
                total=self.data["total"],
                page=self.data["page"],
                page_size=self.data["page_size"],
                total_pages=(self.data["total"] + self.data["page_size"] - 1) // self.data["page_size"]
            )
        return None
    
    @property
    def total(self) -> int:
        """获取总记录数"""
        if isinstance(self.data, dict) and "total" in self.data:
            return self.data["total"]
        if self.pagination:
            return self.pagination.total
        return len(self.items)


class HSIndustryCompanyStats(BaseModel):
    """恒生行业公司统计"""
    total_companies: int = Field(..., description="公司总数")
    level1_stats: List[Dict[str, Any]] = Field(..., description="一级行业统计")
    level2_stats: List[Dict[str, Any]] = Field(..., description="二级行业统计")


class HSIndustryCompanyStatsResponse(StandardResponseDTO):
    """恒生行业公司统计响应"""
    
    def __init__(self, **data):
        """初始化方法，处理没有data字段的情况"""
        # 如果传入的数据没有data字段，则将整个数据作为data
        if "data" not in data:
            super().__init__(status=data.get("status", "success"), data=data)
        else:
            super().__init__(**data)
    
    @property
    def stats(self) -> HSIndustryCompanyStats:
        """获取恒生行业公司统计"""
        if isinstance(self.data, dict):
            return HSIndustryCompanyStats(**self.data)
        # 如果data不是字典，返回空对象
        return HSIndustryCompanyStats.model_construct()