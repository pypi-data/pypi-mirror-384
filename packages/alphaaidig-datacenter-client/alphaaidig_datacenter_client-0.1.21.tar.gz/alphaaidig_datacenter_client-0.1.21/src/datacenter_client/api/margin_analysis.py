from __future__ import annotations
from typing import Optional, Dict, Any, TYPE_CHECKING, List

if TYPE_CHECKING:
    from ..base import BaseClient

from ..dto.margin_analysis import MarginAnalysisListResponse, MarginAnalysisResponse


class MarginAnalysisClient:
    """Client for Margin Analysis related endpoints."""
    def __init__(self, client: "BaseClient"):
        self._client = client

    def page_list(
        self,
        analysis_type: str,
        target_code: str,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> MarginAnalysisListResponse:
        """
        Get a paginated list of margin analysis results.
        Corresponds to GET /margin_analysis/page_list
        
        Args:
            trade_date: Trading date in YYYYMMDD or yyyy-MM-dd format
            start_date: Start date in YYYYMMDD or yyyy-MM-dd format
            end_date: End date in YYYYMMDD or yyyy-MM-dd format (defaults to today if not provided)
            analysis_type: Analysis type (index/industry), required
            target_code: Target code (index code/industry code), required
            page: Page number (default: 1)
            page_size: Number of items per page (default: 50)
            
        Returns:
            MarginAnalysisListResponse: Paginated margin analysis data with type safety
        """
        params: Dict[str, Any] = {"page": page, "page_size": page_size, "analysis_type": analysis_type, "target_code": target_code}
        if trade_date:
            params["trade_date"] = trade_date
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        response_data = self._client._request("GET", "/api/v1/margin_analysis/page_list", params=params)
        return MarginAnalysisListResponse(**response_data)

    def list(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        analysis_type: Optional[str] = None,
        target_codes: Optional[List[str]] = None
    ) -> MarginAnalysisResponse:
        """
        Get a list of margin analysis results without pagination, supports batch query.
        Corresponds to GET /margin_analysis/list
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            analysis_type: Analysis type (index/industry)
            target_codes: List of target codes (index codes/industry codes)
            
        Returns:
            MarginAnalysisResponse: Margin analysis data with type safety
        """
        params: Dict[str, Any] = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if analysis_type:
            params["analysis_type"] = analysis_type
        if target_codes:
            params["target_codes"] = target_codes
        
        response_data = self._client._request("GET", "/api/v1/margin_analysis/list", params=params)
        return MarginAnalysisResponse(**response_data)