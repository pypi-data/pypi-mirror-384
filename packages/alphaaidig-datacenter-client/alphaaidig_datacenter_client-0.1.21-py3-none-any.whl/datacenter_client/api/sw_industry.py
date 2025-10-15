from __future__ import annotations
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..base import BaseClient

from ..dto import (
    SWIndustryLevel1ListResponse,
    SWIndustryLevel2ListResponse,
    SWIndustryLevel3ListResponse,
    SWIndustryAllResponse
)


class SWIndustryClient:
    """Client for SW-Industry related endpoints."""
    def __init__(self, client: "BaseClient"):
        self._client = client

    def get_level1_list(
        self
    ) -> SWIndustryLevel1ListResponse:
        """
        Get a list of SW level1 industries.
        Corresponds to GET /api/v1/sw_industry/level1/list
        """
        response = self._client._request("GET", "/api/v1/sw_industry/level1/list")
        return SWIndustryLevel1ListResponse(**response)

    def get_level2_list(
        self,
        level1_code: Optional[str] = None
    ) -> SWIndustryLevel2ListResponse:
        """
        Get a list of SW level2 industries.
        Corresponds to GET /api/v1/sw_industry/level2/list
        """
        params: Dict[str, Any] = {}
        if level1_code:
            params["level1_code"] = level1_code
        
        response = self._client._request("GET", "/api/v1/sw_industry/level2/list", params=params)
        return SWIndustryLevel2ListResponse(**response)

    def get_level3_list(
        self,
        level1_code: Optional[str] = None,
        level2_code: Optional[str] = None
    ) -> SWIndustryLevel3ListResponse:
        """
        Get a list of SW level3 industries.
        Corresponds to GET /api/v1/sw_industry/level3/list
        """
        params: Dict[str, Any] = {}
        if level1_code:
            params["level1_code"] = level1_code
        if level2_code:
            params["level2_code"] = level2_code
        
        response = self._client._request("GET", "/api/v1/sw_industry/level3/list", params=params)
        return SWIndustryLevel3ListResponse(**response)

    def get_all_industries(
        self
    ) -> SWIndustryAllResponse:
        """
        Get all SW industries.
        Corresponds to GET /api/v1/sw_industry/all
        """
        response = self._client._request("GET", "/api/v1/sw_industry/all")
        return SWIndustryAllResponse(**response)