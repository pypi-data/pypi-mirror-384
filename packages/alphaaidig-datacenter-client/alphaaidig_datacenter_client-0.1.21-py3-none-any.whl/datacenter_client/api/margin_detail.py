from __future__ import annotations
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..base import BaseClient

from ..dto.margin_detail import MarginDetailListResponse


class MarginDetailClient:
    """Client for Margin Detail related endpoints."""
    def __init__(self, client: "BaseClient"):
        self._client = client

    def page_list_by_date(
        self,
        trade_date: str,
        stock_code: Optional[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> MarginDetailListResponse:
        """
        Get a paginated list of margin details by date range.
        Corresponds to GET /margin_detail/page_list_by_date
        
        Args:
            trade_date: trade date in YYYY-MM-DD format
            exchange_id: Exchange ID
            page: Page number (default: 1)
            page_size: Number of items per page (default: 10)
            
        Returns:
            MarginDetailListResponse containing paginated margin detail data by date
        """
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        params["trade_date"] = trade_date
        if stock_code:
            params["stock_code"] = stock_code
        
        response_data = self._client._request("GET", "/api/v1/margin_detail/page_list_by_date", params=params)
        return MarginDetailListResponse(**response_data)

    def page_list_by_stock(
        self,
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> MarginDetailListResponse:
        """
        Get a paginated list of margin details by stock code.
        Corresponds to GET /margin_detail/page_list_by_stock
        
        Args:
            stock_code: Stock code
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            page: Page number (default: 1)
            page_size: Number of items per page (default: 10)
            
        Returns:
            MarginDetailListResponse containing paginated margin detail data by stock
        """
        params: Dict[str, Any] = {"stock_code": stock_code, "page": page, "page_size": page_size}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        response_data = self._client._request("GET", "/api/v1/margin_detail/page_list_by_stock", params=params)
        return MarginDetailListResponse(**response_data)
        
    def list_by_stock(
        self,
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> MarginDetailListResponse:
        """
        Get a complete list of margin details by stock code (no pagination).
        Corresponds to GET /margin_detail/list_by_stock
        
        Args:
            stock_code: Stock code
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            MarginDetailListResponse containing complete margin detail data by stock
        """
        params: Dict[str, Any] = {"stock_code": stock_code}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        response_data = self._client._request("GET", "/api/v1/margin_detail/list_by_stock", params=params)
        return MarginDetailListResponse(**response_data)