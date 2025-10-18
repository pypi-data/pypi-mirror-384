import os
from typing import Optional

from deprecated import deprecated

from planqk.api.credentials import DefaultCredentialsProvider
from planqk.api.sdk import PlanqkApi
from planqk.api.sdk.data_pools.client import DataPoolsClient

_BASE_URL = "KQH_BASE_URL"


class PlanqkApiClient:
    def __init__(self, access_token: Optional[str] = None, organization_id: Optional[str] = None):
        base_url = os.environ.get(_BASE_URL, "https://api.hub.kipu-quantum.com/qc-catalog")
        credentials_provider = DefaultCredentialsProvider(access_token)

        self.api = PlanqkApi(base_url=base_url, api_key=credentials_provider.get_access_token(), organization_id=organization_id)

    @property
    @deprecated(version="1.3.0", reason="Use `api.data_pools` instead.")
    def data_pools(self) -> DataPoolsClient:
        return self.api.data_pools
