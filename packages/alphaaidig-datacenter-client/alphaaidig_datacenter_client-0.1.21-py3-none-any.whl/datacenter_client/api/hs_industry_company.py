"""
恒生行业公司API客户端
"""
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..base import BaseClient

from ..dto.hs_industry_company import (
    HSIndustryCompanyListResponse,
    HSIndustryCompanyDetailResponse,
    HSIndustryCompanyByIndustryResponse
)


class HSIndustryCompanyClient:
    """恒生行业公司API客户端"""
    def __init__(self, client: "BaseClient"):
        self._client = client

    def get_page_list(
        self,
        page: int = 1,
        page_size: int = 50,
        stock_code: Optional[str] = None,
        stock_name: Optional[str] = None,
        level1_industry_code: Optional[str] = None,
        level2_industry_code: Optional[str] = None,
        level1_industry_name: Optional[str] = None,
        level2_industry_name: Optional[str] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> HSIndustryCompanyListResponse:
        """
        恒生行业公司分页查询
        
        Args:
            page: 页码
            page_size: 每页数量
            stock_code: 股票代码过滤条件
            stock_name: 股票名称过滤条件
            level1_industry_code: 一级行业代码过滤条件
            level2_industry_code: 二级行业代码过滤条件
            level1_industry_name: 一级行业名称过滤条件
            level2_industry_name: 二级行业名称过滤条件
            order_by: 排序字段，支持 level1_industry_code、level2_industry_code、stock_code、stock_name
            order_desc: 是否降序排序
            
        Returns:
            HSIndustryCompanyListResponse: 响应结果
        """
        params: Dict[str, Any] = {
            "page": page,
            "page_size": page_size
        }
        
        if stock_code is not None:
            params["stock_code"] = stock_code
        if stock_name is not None:
            params["stock_name"] = stock_name
        if level1_industry_code is not None:
            params["level1_industry_code"] = level1_industry_code
        if level2_industry_code is not None:
            params["level2_industry_code"] = level2_industry_code
        if level1_industry_name is not None:
            params["level1_industry_name"] = level1_industry_name
        if level2_industry_name is not None:
            params["level2_industry_name"] = level2_industry_name
        if order_by is not None:
            params["order_by"] = order_by
        if order_desc:
            params["order_desc"] = order_desc
        
        response = self._client._request("GET", "/api/v1/hs_industry_company/page_list", params=params)
        return HSIndustryCompanyListResponse(**response)
    
    def get_list(
        self,
        stock_code: Optional[str] = None,
        stock_name: Optional[str] = None,
        level1_industry_code: Optional[str] = None,
        level2_industry_code: Optional[str] = None,
        level1_industry_name: Optional[str] = None,
        level2_industry_name: Optional[str] = None
    ) -> HSIndustryCompanyListResponse:
        """
        恒生行业公司列表查询（不带分页）
        
        Args:
            stock_code: 股票代码过滤条件
            stock_name: 股票名称过滤条件
            level1_industry_code: 一级行业代码过滤条件
            level2_industry_code: 二级行业代码过滤条件
            level1_industry_name: 一级行业名称过滤条件
            level2_industry_name: 二级行业名称过滤条件
            
        Returns:
            HSIndustryCompanyListResponse: 响应结果
        """
        params: Dict[str, Any] = {}
        
        if stock_code is not None:
            params["stock_code"] = stock_code
        if stock_name is not None:
            params["stock_name"] = stock_name
        if level1_industry_code is not None:
            params["level1_industry_code"] = level1_industry_code
        if level2_industry_code is not None:
            params["level2_industry_code"] = level2_industry_code
        if level1_industry_name is not None:
            params["level1_industry_name"] = level1_industry_name
        if level2_industry_name is not None:
            params["level2_industry_name"] = level2_industry_name
        
        response = self._client._request("GET", "/api/v1/hs_industry_company/list", params=params)
        return HSIndustryCompanyListResponse(**response)
    
    def get_company_detail(self, stock_code: str) -> HSIndustryCompanyDetailResponse:
        """
        获取恒生行业公司详情
        
        Args:
            stock_code: 股票代码
            
        Returns:
            HSIndustryCompanyDetailResponse: 响应结果
        """
        response = self._client._request("GET", f"/api/v1/hs_industry_company/detail/{stock_code}")
        return HSIndustryCompanyDetailResponse(**response)
    
    # 向后兼容的方法
    def get_company_list(
        self,
        page: int = 1,
        page_size: int = 20,
        stock_code: Optional[str] = None,
        stock_name: Optional[str] = None,
        level1_industry_code: Optional[str] = None,
        level2_industry_code: Optional[str] = None,
        level1_industry_name: Optional[str] = None,
        level2_industry_name: Optional[str] = None
    ) -> HSIndustryCompanyListResponse:
        """
        获取恒生行业公司列表（向后兼容方法）
        
        Args:
            page: 页码
            page_size: 每页数量
            stock_code: 股票代码过滤条件
            stock_name: 股票名称过滤条件
            level1_industry_code: 一级行业代码过滤条件
            level2_industry_code: 二级行业代码过滤条件
            level1_industry_name: 一级行业名称过滤条件
            level2_industry_name: 二级行业名称过滤条件
            
        Returns:
            HSIndustryCompanyListResponse: 响应结果
        """
        return self.get_page_list(
            page=page,
            page_size=page_size,
            stock_code=stock_code,
            stock_name=stock_name,
            level1_industry_code=level1_industry_code,
            level2_industry_code=level2_industry_code,
            level1_industry_name=level1_industry_name,
            level2_industry_name=level2_industry_name
        )
    
    