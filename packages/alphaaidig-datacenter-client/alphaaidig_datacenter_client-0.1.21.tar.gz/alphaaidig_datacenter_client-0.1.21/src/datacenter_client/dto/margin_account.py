"""
融资融券账户相关的数据传输对象（DTO）
"""
from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field

from .base import PaginationInfoDTO, StandardResponseDTO, StandardListResponseDTO, TimestampFields, IdFields


class MarginAccountItem(BaseModel, TimestampFields, IdFields):
    """融资融券账户统计项"""
    trade_date: str = Field(..., description="交易日期（格式：YYYY-MM-DD）")
    financing_balance: Optional[int] = Field(None, description="融资余额(元)")
    margin_balance: Optional[int] = Field(None, description="融券余额(元)")
    financing_purchase: Optional[int] = Field(None, description="融资买入额(元)")
    margin_sell: Optional[int] = Field(None, description="融券卖出额(元)")
    securities_company_count: Optional[int] = Field(None, description="证券公司数量(家)")
    business_department_count: Optional[int] = Field(None, description="营业部数量(个)")
    individual_investor_count: Optional[int] = Field(None, description="个人投资者数量(户)")
    institutional_investor_count: Optional[int] = Field(None, description="机构投资者数量(户)")
    trading_investor_count: Optional[int] = Field(None, description="参与交易的投资者数量(户)")
    indebted_investor_count: Optional[int] = Field(None, description="有融资融券负债的投资者数量(户)")
    collateral_value: Optional[int] = Field(None, description="担保物总价值(元)")
    maintenance_ratio: Optional[float] = Field(None, description="平均维持担保比例(%)")


class MarginAccountListResponse(StandardListResponseDTO):
    """融资融券账户统计列表响应"""
    
    def __init__(self, **data):
        """初始化方法，处理没有data字段的情况"""
        # 如果传入的数据没有data字段，但有items或pagination字段，则将整个数据作为data
        if "data" not in data and ("items" in data or "pagination" in data):
            super().__init__(status=data.get("status", "success"), data=data)
        else:
            super().__init__(**data)
    
    @property
    def items(self) -> List[MarginAccountItem]:
        """获取融资融券账户统计项列表"""
        if isinstance(self.data, dict) and "items" in self.data:
            return [MarginAccountItem(**item) if isinstance(item, dict) else item for item in self.data["items"]]
        elif isinstance(self.data, list):
            # 如果data直接是列表
            return [MarginAccountItem(**item) if isinstance(item, dict) else item for item in self.data]
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


class MarginAccountResponse(StandardResponseDTO):
    """融资融券账户统计响应"""
    
    def __init__(self, **data):
        """初始化方法，处理没有data字段的情况"""
        # 如果传入的数据没有data字段，但有items或total字段，则将整个数据作为data
        if "data" not in data and ("items" in data or "total" in data):
            super().__init__(status=data.get("status", "success"), data=data)
        else:
            super().__init__(**data)
    
    @property
    def items(self) -> List[MarginAccountItem]:
        """获取融资融券账户统计项列表"""
        if isinstance(self.data, dict) and "items" in self.data:
            items_data = self.data["items"]
            return [MarginAccountItem(**item) if isinstance(item, dict) else item for item in items_data]
        elif isinstance(self.data, list):
            # 如果data直接是列表
            return [MarginAccountItem(**item) if isinstance(item, dict) else item for item in self.data]
        return []
    
    @property
    def total(self) -> int:
        """获取总记录数"""
        if isinstance(self.data, dict) and "total" in self.data:
            return self.data["total"]
        elif isinstance(self.data, list):
            # 如果data直接是列表
            return len(self.data)
        return 0