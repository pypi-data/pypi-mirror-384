# Copyright © 2025 Contrast Security, Inc.
# See https://www.contrastsecurity.com/enduser-terms-0317a for more details.
from __future__ import annotations
from collections.abc import Mapping
from typing import Callable

from contrast_fireball import OtelAttributes, SpanType

from contrast.agent.policy.handlers import EventDict


def authz_span_attrs_builder(
    event_dict: EventDict,
) -> tuple[SpanType, Callable[[Mapping[str, object], object], OtelAttributes], None]:
    dac_perm_param_location = str(event_dict.get("dac_perm", ""))
    if not dac_perm_param_location:
        raise ValueError("Event must specify 'dac_perm'.")

    def observe_span_attrs(args: Mapping[str, object], result: object):
        attrs = {"contrast.authorization.mechanism": "dac"}
        if perm := str(args.get(dac_perm_param_location, "")):
            attrs["contrast.authorization.dac.permission"] = perm.lower()
        return attrs

    return SpanType.AuthorizationRequest, observe_span_attrs, None
