from __future__ import annotations
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..base import BaseClient

from ..dto.margin_account import (
    MarginAccountListResponse,
    MarginAccountResponse
)


class MarginAccountClient:
    """Client for Margin Account related endpoints."""
    def __init__(self, client: "BaseClient"):
        self._client = client

    def page_list(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> MarginAccountListResponse:
        """
        Get a paginated list of margin account statistics.
        Corresponds to GET /margin_account/page_list
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            page: Page number (default: 1)
            page_size: Number of items per page (default: 10)
            
        Returns:
            MarginAccountListResponse containing paginated margin account data
        """
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        response_data = self._client._request("GET", "/api/v1/margin_account/page_list", params=params)
        return MarginAccountListResponse(**response_data)

    def list(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> MarginAccountResponse:
        """
        Get a list of margin account statistics without pagination.
        Corresponds to GET /margin_account/list
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            limit: Maximum number of records to return
            
        Returns:
            MarginAccountResponse containing margin account data
        """
        params: Dict[str, Any] = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if limit:
            params["limit"] = limit
        
        response_data = self._client._request("GET", "/api/v1/margin_account/list", params=params)
        return MarginAccountResponse(**response_data)