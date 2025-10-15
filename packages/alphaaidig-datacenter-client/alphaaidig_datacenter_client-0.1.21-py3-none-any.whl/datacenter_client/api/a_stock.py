from __future__ import annotations
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..base import BaseClient

from ..dto.a_stock import (
    AStockListResponse,
    AStockResponse,
    AStockSummaryResponse
)


class AStockClient:
    """Client for A-Stock related endpoints."""
    def __init__(self, client: "BaseClient"):
        self._client = client

    def page_list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        exchange: Optional[str] = None
    ) -> AStockListResponse:
        """
        Get a paginated list of A-stocks.
        Corresponds to GET /a_stock/page_list
        
        Returns:
            AStockListResponse containing paginated A-stock data
        """
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if search:
            params["search"] = search
        if exchange:
            params["exchange"] = exchange
        
        response_data = self._client._request("GET", "/api/v1/a_stock/page_list", params=params)
        return AStockListResponse(**response_data)

    def get(self, stock_code: str) -> AStockResponse:
        """
        Get details for a specific A-stock by its code.
        Corresponds to GET /a_stock/{stock_code}
        
        Returns:
            AStockResponse containing A-stock details
        """
        response_data = self._client._request("GET", f"/api/v1/a_stock/{stock_code}")
        return AStockResponse(**response_data)

    def summary(self) -> AStockSummaryResponse:
        """
        Get statistical summary of A-stocks.
        Corresponds to GET /a_stock/stats/summary
        
        Returns:
            AStockSummaryResponse containing A-stock statistical summary
        """
        response_data = self._client._request("GET", "/api/v1/a_stock/stats/summary")
        return AStockSummaryResponse(**response_data)