# Copyright © 2025 Contrast Security, Inc.
# See https://www.contrastsecurity.com/enduser-terms-0317a for more details.
from __future__ import annotations
from contrast.agent.agent_lib.input_tracing import InputAnalysisResult
from contrast.agent.protect.rule.base_rule import BaseRule

from contrast.api.sample import Sample
from contrast_vendor import structlog as logging

logger = logging.getLogger("contrast")


class Ssrf(BaseRule):
    """
    Ssrf Protection rule
    Currently in BETA.
    """

    RULE_NAME = "ssrf"

    def is_postfilter(self):
        return False

    def build_sample(
        self,
        evaluation: InputAnalysisResult | None,
        candidate_string: str | None,
        **kwargs,
    ) -> Sample:
        assert evaluation is not None
        url = candidate_string
        sample = self.build_base_sample(evaluation)
        if url is not None:
            sample.details["url"] = url
        return sample
