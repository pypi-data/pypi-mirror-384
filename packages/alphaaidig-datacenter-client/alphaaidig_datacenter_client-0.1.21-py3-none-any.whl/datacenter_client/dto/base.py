"""
客户端数据传输对象（DTO）基础模型
"""
from typing import Any, Generic, TypeVar, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseDTO(BaseModel):
    """基础DTO类"""
    class Config:
        """Pydantic配置"""
        use_enum_values = True
        validate_assignment = True


class PaginationInfoDTO(BaseDTO):
    """分页信息DTO"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")


class BaseResponseDTO(BaseDTO):
    """基础响应DTO"""
    status: str = Field("success", description="响应状态")
    message: Optional[str] = Field(None, description="响应消息")
    data: Any = Field(None, description="响应数据")


class StandardResponseDTO(BaseDTO):
    """标准响应DTO"""
    status: str = Field("success", description="响应状态")
    data: Any = Field(..., description="响应数据")
    
    @property
    def is_success(self) -> bool:
        """检查响应是否成功"""
        return self.status == "success"


class StandardListResponseDTO(BaseDTO):
    """标准列表响应DTO"""
    status: str = Field("success", description="响应状态")
    data: dict = Field(..., description="响应数据")
    
    @property
    def is_success(self) -> bool:
        """检查响应是否成功"""
        return self.status == "success"


class PaginatedResponseDTO(BaseDTO, Generic[T]):
    """分页响应DTO"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    items: List[T] = Field(..., description="数据项列表")
    
    @property
    def total_pages(self) -> int:
        """计算总页数"""
        return (self.total + self.size - 1) // self.size


class TimestampFields:
    """时间戳字段混入类，为DTO添加创建和更新时间字段"""
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class IdFields:
    """ID字段混入类，为DTO添加ID字段"""
    id: int = Field(..., description="记录ID")