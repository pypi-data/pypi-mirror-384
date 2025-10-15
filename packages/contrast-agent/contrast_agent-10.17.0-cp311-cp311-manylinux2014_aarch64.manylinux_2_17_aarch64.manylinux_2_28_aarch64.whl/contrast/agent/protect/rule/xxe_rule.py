# Copyright © 2025 Contrast Security, Inc.
# See https://www.contrastsecurity.com/enduser-terms-0317a for more details.
from __future__ import annotations
import re

from contrast.agent.agent_lib.input_tracing import InputAnalysisResult
from contrast.agent.policy.patch_location_policy import PatchLocationPolicy
from contrast.agent.protect.rule.base_rule import AnalysisStage, BaseRule
from contrast.agent.protect.rule.xxe.entity_wrapper import EntityWrapper
from contrast.api.attack import Attack
from contrast.api.user_input import UserInput, InputType
from contrast.api.sample import Sample
from contrast.utils.patch_utils import get_arg


class Xxe(BaseRule):
    """
    XXE Protection rule
    """

    RULE_NAME = "xxe"
    INPUT_NAME = "XML Prolog"

    EXTERNAL_ENTITY_PATTERN = re.compile(
        r"<!ENTITY\s+[a-zA-Z0-f]+\s+(?:SYSTEM|PUBLIC)\s+(.*?)>"
    )

    def __init__(self):
        super().__init__()

        self.prolog_xml = None

    def is_prefilter(self):
        return False

    def is_postfilter(self):
        return False

    def skip_protect_analysis(
        self, user_input: object, args: tuple, kwargs: dict[str, object]
    ) -> bool:
        return bool(
            (parser := get_arg(args, kwargs, 1, "parser", None))
            and getattr(parser, "resolve_entities", None) is False
        )

    def find_attack(
        self,
        candidate_string: str | None = None,
        analysis_stage: AnalysisStage | None = None,
        **kwargs,
    ) -> Attack | None:
        assert candidate_string is not None
        last_idx = 0
        declared_entities = []
        entities_resolved = []

        for match in self.EXTERNAL_ENTITY_PATTERN.finditer(candidate_string):
            last_idx = match.end(0)

            entity_wrapper = EntityWrapper(match.group())
            if not entity_wrapper.is_external_entity():
                continue

            declared_entities.append(self._build_match(match.group(), last_idx))
            entities_resolved.append(self._build_wrapper(entity_wrapper))

        self.prolog_xml = candidate_string[:last_idx]
        if not self.prolog_xml:
            return None

        attack = self.build_attack_with_match(
            candidate_string,
            declared_entities=declared_entities,
            entities_resolved=entities_resolved,
        )
        return attack

    def _build_match(self, match_string: str, end_idx: int) -> dict[str, int]:
        return {"start": end_idx - len(match_string), "end": end_idx}

    def _build_wrapper(self, entity: EntityWrapper) -> dict[str, str]:
        return {"systemId": entity.system_id, "publicId": entity.public_id}

    def build_sample(
        self,
        evaluation: InputAnalysisResult | None,
        candidate_string: str | None,
        **kwargs,
    ) -> Sample:
        sample = self.build_base_sample(evaluation)
        declared_entities = kwargs["declared_entities"]
        if declared_entities:
            sample.details["declaredEntities"] = declared_entities

        entities_resolved = kwargs["entities_resolved"]
        if entities_resolved:
            sample.details["entitiesResolved"] = entities_resolved

        sample.details["xml"] = self.prolog_xml
        return sample

    def build_user_input(self, evaluation: InputAnalysisResult) -> UserInput:
        assert self.prolog_xml is not None
        return UserInput(
            type=InputType.UNKNOWN,
            name=self.INPUT_NAME,
            value=self.prolog_xml,
        )

    def infilter_kwargs(self, user_input: str, patch_policy: PatchLocationPolicy):
        return dict(framework=patch_policy.method_name)
