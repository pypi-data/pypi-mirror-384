# Copyright © 2025 Contrast Security, Inc.
# See https://www.contrastsecurity.com/enduser-terms-0317a for more details.
from contrast.agent.assess.rules.response.base_response_rule import BaseResponseRule
from contrast.agent.assess.rules import build_finding, send_finding


class BaseHeaderOnlyRule(BaseResponseRule):
    @property
    def name(self):
        raise NotImplementedError

    @property
    def header_key(self):
        raise NotImplementedError

    @property
    def good_values(self):
        raise NotImplementedError

    def is_violated(self, headers, *args):
        header_violated, header_properties = self.is_header_violated(headers)
        if not header_violated:
            return False, {}

        return True, header_properties

    def is_header_violated(self, headers):
        value = headers.get(self.header_key)
        if not value:
            # Finding gets no properties if header is missing
            return True, {}

        if value not in self.good_values:
            properties = dict(
                type="Header",
                name=self.header_key,
                value=value,
            )
            return True, properties

        return False, None

    def create_finding(self, properties):
        """
        header-only rules report data=str, where str is the value
        the header is set to. This is unlike other response rules that
        report data=[]
        """
        if not properties:
            data = dict(data="")
        else:
            data = dict(data=f"{properties.get('value')}")
        return build_finding(self, data)

    def build_and_append_finding(self, properties, context):
        finding = self.create_finding(properties)
        send_finding(finding, context)
