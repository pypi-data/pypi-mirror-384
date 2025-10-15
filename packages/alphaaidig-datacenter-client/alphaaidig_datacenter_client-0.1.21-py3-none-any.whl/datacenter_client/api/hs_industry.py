from __future__ import annotations
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..base import BaseClient

from ..dto.hs_industry import (
    HSIndustryLevel1ListResponse,
    HSIndustryLevel2ListResponse,
    HSIndustryLevel3ListResponse,
    HSIndustryAllResponse,
    HSIndustrySummaryResponse
)


class HSIndustryClient:
    """Client for HS-Industry related endpoints."""
    def __init__(self, client: "BaseClient"):
        self._client = client

    def get_level1_list(
        self
    ) -> HSIndustryLevel1ListResponse:
        """
        Get a list of HS level1 industries.
        Corresponds to GET /api/v1/hs_industry/level1/list
        """
        response = self._client._request("GET", "/api/v1/hs_industry/level1/list")
        return HSIndustryLevel1ListResponse(**response)

    def get_level2_list(
        self,
        level1_code: Optional[str] = None
    ) -> HSIndustryLevel2ListResponse:
        """
        Get a list of HS level2 industries.
        Corresponds to GET /api/v1/hs_industry/level2/list
        """
        params: Dict[str, Any] = {}
        if level1_code:
            params["level1_code"] = level1_code
        
        response = self._client._request("GET", "/api/v1/hs_industry/level2/list", params=params)
        return HSIndustryLevel2ListResponse(**response)

    def get_level3_list(
        self,
        level1_code: Optional[str] = None,
        level2_code: Optional[str] = None
    ) -> HSIndustryLevel3ListResponse:
        """
        Get a list of HS level3 industries.
        Corresponds to GET /api/v1/hs_industry/level3/list
        """
        params: Dict[str, Any] = {}
        if level1_code:
            params["level1_code"] = level1_code
        if level2_code:
            params["level2_code"] = level2_code
        
        response = self._client._request("GET", "/api/v1/hs_industry/level3/list", params=params)
        return HSIndustryLevel3ListResponse(**response)

    def get_all_industries(
        self
    ) -> HSIndustryAllResponse:
        """
        Get all HS industries.
        Corresponds to GET /api/v1/hs_industry/all
        """
        response = self._client._request("GET", "/api/v1/hs_industry/all")
        return HSIndustryAllResponse(**response)

    def get_summary(
        self
    ) -> HSIndustrySummaryResponse:
        """
        Get statistical summary of HS-industries.
        Corresponds to GET /api/v1/hs_industry/stats/summary
        
        Returns:
            HSIndustrySummaryResponse containing HS-industry statistical summary
        """
        response_data = self._client._request("GET", "/api/v1/hs_industry/stats/summary")
        return HSIndustrySummaryResponse(**response_data)