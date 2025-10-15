from typing import Optional

from .base import BaseClient
from .api.a_stock import AStockClient
from .api.hk_stock import HKStockClient
from .api.hs_industry import HSIndustryClient
from .api.hs_industry_company import HSIndustryCompanyClient
from .api.margin_account import MarginAccountClient
from .api.margin_detail import MarginDetailClient

from .api.margin_analysis import MarginAnalysisClient
from .api.sw_industry import SWIndustryClient
from .api.sw_industry_company import SWIndustryCompanyClient

class DatacenterClient(BaseClient):
    """
    The main client for interacting with all Datacenter API services.
    
    This client provides access to different API resource groups (e.g., A-stocks, HK-stocks, etc.)
    through dedicated sub-clients.
    
    Usage:
        with DatacenterClient(base_url="...") as client:
            stocks = client.a_stock.list()
    """
    def __init__(self, base_url: str, token: Optional[str] = None, timeout: int = 30):
        """
        Initializes the main client.

        Args:
            base_url: The base URL for the API, e.g., "http://localhost:10000".
            token: An optional token for authentication.
            timeout: The request timeout in seconds.
        """
        super().__init__(base_url, token, timeout)
        
        # Initialize sub-clients for each API resource
        self.a_stock = AStockClient(self)
        self.hk_stock = HKStockClient(self)
        self.hs_industry = HSIndustryClient(self)
        self.hs_industry_company = HSIndustryCompanyClient(self)
        self.margin_account = MarginAccountClient(self)
        self.margin_detail = MarginDetailClient(self)

        self.margin_analysis = MarginAnalysisClient(self)
        self.sw_industry = SWIndustryClient(self)
        self.sw_industry_company = SWIndustryCompanyClient(self)