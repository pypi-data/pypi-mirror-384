# Copyright © 2025 Contrast Security, Inc.
# See https://www.contrastsecurity.com/enduser-terms-0317a for more details.
from contrast.agent.protect.rule.base_rule import BaseRule
from contrast.agent.protect.rule.mode import Mode


class MalformedHeader(BaseRule):
    """
    Malformed Header Protection rule
    """

    RULE_NAME = "malformed-header"

    @property
    def mode(self):
        """
        Always block at perimeter
        """
        return Mode.BLOCK_AT_PERIMETER
