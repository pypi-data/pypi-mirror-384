# Copyright © 2025 Contrast Security, Inc.
# See https://www.contrastsecurity.com/enduser-terms-0317a for more details.
import requests

from .base_ts_message import BaseTsAppMessage
from contrast.utils.decorators import fail_loudly
from contrast_vendor import structlog as logging

logger = logging.getLogger("contrast")


class EffectiveConfig(BaseTsAppMessage):
    def __init__(self):
        super().__init__()
        self.base_url = f"{self.settings.api_url}/agents/v1.0/"

        self.body = self.settings.generate_effective_config()

    @property
    def name(self):
        return "effective-config"

    @property
    def path(self):
        return (
            f"applications/{self.server_name_b64}/{self.server_path_b64}"
            f"/{self.server_type_b64}/{self.app_language_b64}/{self.app_name_b64}"
            "/effective-config"
        )

    @property
    def request_method(self):
        return requests.put

    @fail_loudly("Failed to process Effective Configuration response")
    def process_response(self, response, reporting_client):
        self.process_response_code(response, reporting_client)
