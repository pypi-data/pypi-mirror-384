# Copyright © 2025 Contrast Security, Inc.
# See https://www.contrastsecurity.com/enduser-terms-0317a for more details.
import functools
from typing import Callable
from contrast.applies import apply_rule
from contrast.utils.patch_utils import add_watermark
from contrast.agent.policy import patch_manager
from contrast.agent.policy.patch_location_policy import PatchLocationPolicy

from contrast_vendor import structlog as logging

logger = logging.getLogger("contrast")


def build_protect_patch(original_func: Callable, patch_policy: PatchLocationPolicy):
    @functools.wraps(original_func)
    def protect_patch(*args, **kwargs):
        """
        Protect patch that will run in addition to running original_func.
        If we cannot run the protect rule, at the very least run the original_func.
        """
        return apply_rule(patch_policy, original_func, args, kwargs)

    return add_watermark(protect_patch)


def apply_protect_patch(patch_site: object, patch_policy: PatchLocationPolicy):
    logger.debug("Applying protect patch to %s", patch_policy.name)

    original_func = getattr(patch_site, patch_policy.method_name)

    patch_manager.patch(
        patch_site,
        patch_policy.method_name,
        build_protect_patch(original_func, patch_policy),
    )
