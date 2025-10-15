"""
融资融券明细相关的数据传输对象（DTO）
"""
from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field

from .base import PaginationInfoDTO, StandardResponseDTO, StandardListResponseDTO, TimestampFields, IdFields


class MarginDetailItem(BaseModel, TimestampFields, IdFields):
    """融资融券明细项"""
    trade_date: str = Field(..., description="交易日期（格式：YYYY-MM-DD）")
    stock_code: str = Field(..., description="股票代码")
    stock_name: Optional[str] = Field(None, description="股票名称")
    exchange_id: Optional[str] = Field(None, description="交易所代码")
    rz_balance: Optional[int] = Field(None, description="融资余额(元)")
    rq_balance: Optional[int] = Field(None, description="融券余额(元)")
    rq_volume: Optional[int] = Field(None, description="融券余量(股)")
    rz_buy_amount: Optional[int] = Field(None, description="融资买入额(元)")
    rq_sell_amount: Optional[int] = Field(None, description="融券卖出额(元)")
    rz_repay_amount: Optional[int] = Field(None, description="融资偿还额(元)")
    rq_repay_volume: Optional[int] = Field(None, description="融券偿还量(股)")
    rz_net_buy_amount: Optional[int] = Field(None, description="融资净买入额(元)")
    rq_net_sell_volume: Optional[int] = Field(None, description="融券净卖出量(股)")


class MarginDetailListResponse(StandardListResponseDTO):
    """融资融券明细列表响应"""
    
    def __init__(self, **data):
        """初始化方法，处理没有data字段的情况"""
        # 如果传入的数据没有data字段，但有items或pagination字段，则将整个数据作为data
        if "data" not in data and ("items" in data or "pagination" in data):
            super().__init__(status=data.get("status", "success"), data=data)
        else:
            super().__init__(**data)
    
    @property
    def items(self) -> List[MarginDetailItem]:
        """获取融资融券明细项列表"""
        if isinstance(self.data, dict) and "items" in self.data:
            return [MarginDetailItem(**item) if isinstance(item, dict) else item for item in self.data["items"]]
        elif isinstance(self.data, list):
            # 如果data直接是列表
            return [MarginDetailItem(**item) if isinstance(item, dict) else item for item in self.data]
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