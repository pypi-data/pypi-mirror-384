"""
恒生行业相关的数据传输对象（DTO）
"""
from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field

from .base import PaginationInfoDTO, StandardResponseDTO, StandardListResponseDTO, TimestampFields, IdFields


class HSIndustryItem(BaseModel, TimestampFields, IdFields):
    """恒生行业项"""
    level1_industry_code: str = Field(..., description="一级行业代码")
    level1_industry_name: str = Field(..., description="一级行业名称")
    level2_industry_code: Optional[str] = Field(None, description="二级行业代码")
    level2_industry_name: Optional[str] = Field(None, description="二级行业名称")
    level3_industry_code: Optional[str] = Field(None, description="三级行业代码")
    level3_industry_name: Optional[str] = Field(None, description="三级行业名称")
    description: Optional[str] = Field(None, description="行业描述")


class HSIndustryLevel1Item(BaseModel):
    """恒生一级行业项"""
    industry_code: str = Field(..., description="行业代码")
    name: str = Field(..., description="行业名称")


class HSIndustryLevel2Item(BaseModel):
    """恒生二级行业项"""
    industry_code: str = Field(..., description="行业代码")
    name: str = Field(..., description="行业名称")
    level1_industry_code: str = Field(..., description="一级行业代码")
    level1_name: str = Field(..., description="一级行业名称")


class HSIndustryLevel3Item(BaseModel):
    """恒生三级行业项"""
    industry_code: str = Field(..., description="行业代码")
    name: str = Field(..., description="行业名称")
    level1_industry_code: str = Field(..., description="一级行业代码")
    level1_name: str = Field(..., description="一级行业名称")
    level2_industry_code: str = Field(..., description="二级行业代码")
    level2_name: str = Field(..., description="二级行业名称")


class HSIndustryListResponse(StandardListResponseDTO):
    """恒生行业列表响应"""
    
    def __init__(self, **data):
        """初始化方法，处理没有data字段的情况"""
        # 如果传入的数据没有data字段，但有items或pagination字段，则将整个数据作为data
        if "data" not in data and ("items" in data or "pagination" in data):
            super().__init__(status=data.get("status", "success"), data=data)
        else:
            super().__init__(**data)
    
    @property
    def items(self) -> List[HSIndustryItem]:
        """获取恒生行业项列表"""
        if isinstance(self.data, dict) and "items" in self.data:
            return [HSIndustryItem(**item) if isinstance(item, dict) else item for item in self.data["items"]]
        elif isinstance(self.data, list):
            # 如果data直接是列表
            return [HSIndustryItem(**item) if isinstance(item, dict) else item for item in self.data]
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


class HSIndustryLevel1ListResponse(StandardListResponseDTO):
    """恒生一级行业列表响应"""
    
    def __init__(self, **data):
        """初始化方法，处理没有data字段的情况"""
        if "data" not in data and ("items" in data or "pagination" in data):
            super().__init__(status=data.get("status", "success"), data=data)
        else:
            super().__init__(**data)
    
    @property
    def items(self) -> List[HSIndustryLevel1Item]:
        """获取恒生一级行业项列表"""
        if isinstance(self.data, dict) and "items" in self.data:
            return [HSIndustryLevel1Item(**item) if isinstance(item, dict) else item for item in self.data["items"]]
        elif isinstance(self.data, list):
            return [HSIndustryLevel1Item(**item) if isinstance(item, dict) else item for item in self.data]
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


class HSIndustryLevel2ListResponse(StandardListResponseDTO):
    """恒生二级行业列表响应"""
    
    def __init__(self, **data):
        """初始化方法，处理没有data字段的情况"""
        if "data" not in data and ("items" in data or "pagination" in data):
            super().__init__(status=data.get("status", "success"), data=data)
        else:
            super().__init__(**data)
    
    @property
    def items(self) -> List[HSIndustryLevel2Item]:
        """获取恒生二级行业项列表"""
        if isinstance(self.data, dict) and "items" in self.data:
            return [HSIndustryLevel2Item(**item) if isinstance(item, dict) else item for item in self.data["items"]]
        elif isinstance(self.data, list):
            return [HSIndustryLevel2Item(**item) if isinstance(item, dict) else item for item in self.data]
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


class HSIndustryLevel3ListResponse(StandardListResponseDTO):
    """恒生三级行业列表响应"""
    
    def __init__(self, **data):
        """初始化方法，处理没有data字段的情况"""
        if "data" not in data and ("items" in data or "pagination" in data):
            super().__init__(status=data.get("status", "success"), data=data)
        else:
            super().__init__(**data)
    
    @property
    def items(self) -> List[HSIndustryLevel3Item]:
        """获取恒生三级行业项列表"""
        if isinstance(self.data, dict) and "items" in self.data:
            return [HSIndustryLevel3Item(**item) if isinstance(item, dict) else item for item in self.data["items"]]
        elif isinstance(self.data, list):
            return [HSIndustryLevel3Item(**item) if isinstance(item, dict) else item for item in self.data]
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


class HSIndustryAllResponse(StandardResponseDTO):
    """恒生所有行业响应"""
    
    def __init__(self, **data):
        """初始化方法，处理没有data字段的情况"""
        # 如果传入的数据没有data字段，则将整个数据作为data
        if "data" not in data:
            super().__init__(status=data.get("status", "success"), data=data)
        else:
            super().__init__(**data)
    
    @property
    def industries(self) -> List[HSIndustryItem]:
        """获取恒生行业项列表"""
        if isinstance(self.data, dict) and "items" in self.data:
            return [HSIndustryItem(**item) if isinstance(item, dict) else item for item in self.data["items"]]
        elif isinstance(self.data, list):
            # 如果data直接是列表
            return [HSIndustryItem(**item) if isinstance(item, dict) else item for item in self.data]
        return []


class HSIndustryResponse(StandardResponseDTO):
    """恒生行业响应"""
    
    def __init__(self, **data):
        """初始化方法，处理没有data字段的情况"""
        # 如果传入的数据没有data字段，则将整个数据作为data
        if "data" not in data:
            super().__init__(status=data.get("status", "success"), data=data)
        else:
            super().__init__(**data)
    
    @property
    def industry(self) -> HSIndustryItem:
        """获取恒生行业项"""
        if isinstance(self.data, dict):
            return HSIndustryItem(**self.data)
        # 如果data不是字典，返回空对象
        return HSIndustryItem.model_construct()


class HSIndustrySummary(BaseModel):
    """恒生行业统计摘要"""
    total_industries: Optional[int] = Field(None, description="总行业数")
    level_distribution: Optional[Dict[int, int]] = Field(None, description="级别分布")


class HSIndustrySummaryResponse(StandardResponseDTO):
    """恒生行业统计摘要响应"""
    
    def __init__(self, **data):
        """初始化方法，处理没有data字段的情况"""
        # 如果传入的数据没有data字段，则将整个数据作为data
        if "data" not in data:
            super().__init__(status=data.get("status", "success"), data=data)
        else:
            super().__init__(**data)
    
    @property
    def summary(self) -> HSIndustrySummary:
        """获取恒生行业统计摘要"""
        if isinstance(self.data, dict):
            return HSIndustrySummary(**self.data)
        # 如果data不是字典，返回空对象
        return HSIndustrySummary.model_construct()