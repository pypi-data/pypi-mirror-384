"""
融资融券分析相关的数据传输对象（DTO）
"""
from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

from .base import PaginationInfoDTO, StandardResponseDTO, StandardListResponseDTO, TimestampFields, IdFields


class MarginAnalysisItem(BaseModel, TimestampFields, IdFields):
    """融资融券分析结果项"""
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
    rzye: Optional[int] = Field(None, description="融资余额(元)")
    rqye: Optional[int] = Field(None, description="融券余额(元)")
    rzmre: Optional[int] = Field(None, description="融资买入额(元)")
    rqyl: Optional[int] = Field(None, description="融券余量（股）")
    rzche: Optional[int] = Field(None, description="融资偿还额(元)")
    rqchl: Optional[int] = Field(None, description="融券偿还量(股)")
    rqmcl: Optional[int] = Field(None, description="融券卖出量(股,份,手)")
    rzrqye: Optional[int] = Field(None, description="融资融券余额(元)")
    rzjme: Optional[int] = Field(None, description="当日融资净买入额(元)")
    rqjml: Optional[int] = Field(None, description="融券净买入量(股)")


class MarginAnalysisListResponse(StandardListResponseDTO):
    """融资融券分析结果列表响应"""
    
    def __init__(self, **data):
        """初始化方法，处理没有data字段的情况"""
        # 如果传入的数据没有data字段，但有items或pagination字段，则将整个数据作为data
        if "data" not in data and ("items" in data or "pagination" in data):
            super().__init__(status=data.get("status", "success"), data=data)
        else:
            super().__init__(**data)
    
    @property
    def items(self) -> List[MarginAnalysisItem]:
        """获取融资融券分析结果项列表"""
        if isinstance(self.data, dict) and "items" in self.data:
            return [MarginAnalysisItem(**item) if isinstance(item, dict) else item for item in self.data["items"]]
        elif isinstance(self.data, list):
            # 如果data直接是列表
            return [MarginAnalysisItem(**item) if isinstance(item, dict) else item for item in self.data]
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


class MarginAnalysisResponse(StandardResponseDTO):
    """融资融券分析结果响应"""
    
    def __init__(self, **data):
        """初始化方法，处理没有data字段的情况"""
        # 如果传入的数据没有data字段，但有items或total字段，则将整个数据作为data
        if "data" not in data and ("items" in data or "total" in data):
            super().__init__(status=data.get("status", "success"), data=data)
        else:
            super().__init__(**data)
    
    @property
    def items(self) -> List[MarginAnalysisItem]:
        """获取融资融券分析结果项列表"""
        if isinstance(self.data, dict) and "items" in self.data:
            items_data = self.data["items"]
            return [MarginAnalysisItem(**item) if isinstance(item, dict) else item for item in items_data]
        elif isinstance(self.data, list):
            # 如果data直接是列表
            return [MarginAnalysisItem(**item) if isinstance(item, dict) else item for item in self.data]
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