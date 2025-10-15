"""
申万行业相关的数据传输对象（DTO）
"""
from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field

from .base import PaginationInfoDTO, StandardResponseDTO, StandardListResponseDTO, TimestampFields, IdFields


class SWIndustryItem(BaseModel, TimestampFields, IdFields):
    """申万行业项"""
    industry_code: str = Field(..., description="行业代码")
    index_code: str = Field(..., description="指数代码")
    level1_industry: str = Field(..., description="一级行业名称")
    level2_industry: Optional[str] = Field(None, description="二级行业名称")
    level3_industry: Optional[str] = Field(None, description="三级行业名称")
    level1_industry_code: str = Field(..., description="一级行业代码")
    level2_industry_code: Optional[str] = Field(None, description="二级行业代码")
    level3_industry_code: Optional[str] = Field(None, description="三级行业代码")
    level1_index_code: str = Field(..., description="一级指数代码")
    level2_index_code: Optional[str] = Field(None, description="二级指数代码")
    level3_index_code: Optional[str] = Field(None, description="三级指数代码")


class SWIndustryLevel1Item(BaseModel):
    """申万一级行业项"""
    industry_code: str = Field(..., description="行业代码")
    index_code: str = Field(..., description="指数代码")
    name: str = Field(..., description="行业名称")


class SWIndustryLevel2Item(BaseModel):
    """申万二级行业项"""
    industry_code: str = Field(..., description="行业代码")
    index_code: str = Field(..., description="指数代码")
    name: str = Field(..., description="行业名称")
    level1_industry_code: str = Field(..., description="一级行业代码")
    level1_index_code: str = Field(..., description="一级指数代码")
    level1_name: str = Field(..., description="一级行业名称")


class SWIndustryLevel3Item(BaseModel):
    """申万三级行业项"""
    industry_code: str = Field(..., description="行业代码")
    index_code: str = Field(..., description="指数代码")
    name: str = Field(..., description="行业名称")
    level1_industry_code: str = Field(..., description="一级行业代码")
    level1_index_code: str = Field(..., description="一级指数代码")
    level1_name: str = Field(..., description="一级行业名称")
    level2_industry_code: str = Field(..., description="二级行业代码")
    level2_index_code: str = Field(..., description="二级指数代码")
    level2_name: str = Field(..., description="二级行业名称")


class SWIndustryListResponse(StandardListResponseDTO):
    """申万行业列表响应"""
    
    def __init__(self, **data):
        """初始化方法，处理没有data字段的情况"""
        # 如果传入的数据没有data字段，但有items或pagination字段，则将整个数据作为data
        if "data" not in data and ("items" in data or "pagination" in data):
            super().__init__(status=data.get("status", "success"), data=data)
        else:
            super().__init__(**data)
    
    @property
    def items(self) -> List[SWIndustryItem]:
        """获取申万行业项列表"""
        if isinstance(self.data, dict) and "items" in self.data:
            return [SWIndustryItem(**item) if isinstance(item, dict) else item for item in self.data["items"]]
        elif isinstance(self.data, list):
            # 如果data直接是列表
            return [SWIndustryItem(**item) if isinstance(item, dict) else item for item in self.data]
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


class SWIndustryLevel1ListResponse(StandardListResponseDTO):
    """申万一级行业列表响应"""
    
    def __init__(self, **data):
        """初始化方法，处理没有data字段的情况"""
        if "data" not in data and ("items" in data or "pagination" in data):
            super().__init__(status=data.get("status", "success"), data=data)
        else:
            super().__init__(**data)
    
    @property
    def items(self) -> List[SWIndustryLevel1Item]:
        """获取申万一级行业项列表"""
        if isinstance(self.data, dict) and "items" in self.data:
            return [SWIndustryLevel1Item(**item) if isinstance(item, dict) else item for item in self.data["items"]]
        elif isinstance(self.data, list):
            return [SWIndustryLevel1Item(**item) if isinstance(item, dict) else item for item in self.data]
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


class SWIndustryLevel2ListResponse(StandardListResponseDTO):
    """申万二级行业列表响应"""
    
    def __init__(self, **data):
        """初始化方法，处理没有data字段的情况"""
        if "data" not in data and ("items" in data or "pagination" in data):
            super().__init__(status=data.get("status", "success"), data=data)
        else:
            super().__init__(**data)
    
    @property
    def items(self) -> List[SWIndustryLevel2Item]:
        """获取申万二级行业项列表"""
        if isinstance(self.data, dict) and "items" in self.data:
            return [SWIndustryLevel2Item(**item) if isinstance(item, dict) else item for item in self.data["items"]]
        elif isinstance(self.data, list):
            return [SWIndustryLevel2Item(**item) if isinstance(item, dict) else item for item in self.data]
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


class SWIndustryLevel3ListResponse(StandardListResponseDTO):
    """申万三级行业列表响应"""
    
    def __init__(self, **data):
        """初始化方法，处理没有data字段的情况"""
        if "data" not in data and ("items" in data or "pagination" in data):
            super().__init__(status=data.get("status", "success"), data=data)
        else:
            super().__init__(**data)
    
    @property
    def items(self) -> List[SWIndustryLevel3Item]:
        """获取申万三级行业项列表"""
        if isinstance(self.data, dict) and "items" in self.data:
            return [SWIndustryLevel3Item(**item) if isinstance(item, dict) else item for item in self.data["items"]]
        elif isinstance(self.data, list):
            return [SWIndustryLevel3Item(**item) if isinstance(item, dict) else item for item in self.data]
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


class SWIndustryAllResponse(StandardListResponseDTO):
    """申万所有行业数据响应"""
    
    def __init__(self, **data):
        """初始化方法，处理没有data字段的情况"""
        if "data" not in data and ("items" in data or "pagination" in data):
            super().__init__(status=data.get("status", "success"), data=data)
        else:
            super().__init__(**data)
    
    @property
    def items(self) -> List[SWIndustryItem]:
        """获取申万所有行业项列表"""
        if isinstance(self.data, dict) and "items" in self.data:
            return [SWIndustryItem(**item) if isinstance(item, dict) else item for item in self.data["items"]]
        elif isinstance(self.data, list):
            return [SWIndustryItem(**item) if isinstance(item, dict) else item for item in self.data]
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