from __future__ import annotations
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..base import BaseClient

from ..dto.hk_stock import (
    HKStockListResponse,
    HKStockResponse,
    HKStockSummaryResponse
)


class HKStockClient:
    """Client for HK-Stock related endpoints."""
    def __init__(self, client: "BaseClient"):
        self._client = client

    def page_list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        currency: Optional[str] = None,
        suspended: Optional[bool] = None
    ) -> HKStockListResponse:
        """
        Get a paginated list of HK-stocks.
        Corresponds to GET /hk_stock/page_list
        
        Returns:
            HKStockListResponse containing paginated HK-stock data
        """
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if search:
            params["search"] = search
        if currency:
            params["currency"] = currency
        if suspended is not None:
            params["suspended"] = suspended
        
        response_data = self._client._request("GET", "/api/v1/hk_stock/page_list", params=params)
        return HKStockListResponse(**response_data)

    def get(self, stock_code: str) -> HKStockResponse:
        """
        Get details for a specific HK-stock by its code.
        Corresponds to GET /hk_stock/{stock_code}
        
        Returns:
            HKStockResponse containing HK-stock details
        """
        response_data = self._client._request("GET", f"/api/v1/hk_stock/{stock_code}")
        return HKStockResponse(**response_data)

    def summary(self) -> HKStockSummaryResponse:
        """
        Get statistical summary of HK-stocks.
        Corresponds to GET /hk_stock/stats/summary
        
        Returns:
            HKStockSummaryResponse containing HK-stock statistical summary
        """
        response_data = self._client._request("GET", "/api/v1/hk_stock/stats/summary")
        return HKStockSummaryResponse(**response_data)