# Copyright © 2025 Contrast Security, Inc.
# See https://www.contrastsecurity.com/enduser-terms-0317a for more details.
"""
Implementation of patches for the `re` module.

Other methods of the `re` module such as `split` and `escape` can be patched directly,
so they are implemented in policy.
"""

import functools
from contrast_vendor import structlog as logging
import sys


import contrast
from contrast.agent import scope
from contrast.agent.policy import patch_manager, registry
from contrast.agent.assess.apply_trigger import cs__apply_trigger
from contrast.agent.assess.policy.propagators import regex_propagator
from contrast.patches.utils import (
    analyze_policy,
    get_propagation_node,
)
from contrast.utils.decorators import fail_quietly
from contrast.utils.patch_utils import (
    build_and_apply_patch,
    pack_self,
    register_module_patcher,
    unregister_module_patcher,
    wrap_and_watermark,
)

logger = logging.getLogger("contrast")

PATTERN_CLASS = "re.Pattern"
MATCH_CLASS = "re.Match"


def build_group_hook(original_func, patch_policy, propagator):
    del patch_policy

    def group_hook(wrapped, instance, args, kwargs):
        context = contrast.REQUEST_CONTEXT.get()
        result = wrapped(*args, **kwargs)
        if (
            context is not None
            and context.propagate_assess
            and not context.stop_propagation
        ):
            context.propagated()
            with scope.propagation_scope():
                propagator(instance, result, *args)
        return result

    return wrap_and_watermark(original_func, group_hook)


def wrap_repl(repl):
    repl_results = []

    def new_repl(match):
        result = repl(match)
        repl_results.append(result)
        return result

    functools.update_wrapper(new_repl, repl)
    return new_repl, repl_results


@fail_quietly("Failed to propagate sub(n)")
def _analyze_sub(node, retval, repl_results, args, kwargs, new_args):
    if node.method_name == "subn":
        result, count = retval
    else:
        # Account for the fact that count could either be positional or kwarg
        count = args[3] if len(args) == 4 else kwargs.pop("count", 0)
        result = retval

    # Omit count (and flags) if they are part of posargs since they are being passed
    # explicitly to our propagator
    new_args = new_args[:3]
    new_kwargs = dict(count=count)
    if not node.instance_method:
        # Account for the fact that flags could either be positional or kwarg
        new_kwargs["flags"] = args[4] if len(args) > 4 else kwargs.get("flags", 0)

    with scope.propagation_scope():
        regex_propagator.propagate_sub(
            node, result, repl_results, *new_args[:3], **new_kwargs
        )


@fail_quietly("Failed to analyze redos trigger")
def _trigger_redos(name, result, args, kwargs):
    context = contrast.REQUEST_CONTEXT.get()
    if context is None:
        return

    rule = registry.get_triggers_by_rule("redos")

    if not scope.in_trigger_scope() and not scope.in_contrast_or_propagation_scope():
        if rule.disabled:
            # Given how often these patches are called within apps, it's well worth
            # returning early here even though this logic exists further down the stack.
            # However, we MUST call this here after the `in_scope` check because
            # `rule.disabled` calls on Settings code that recursively calls on
            # other patches.
            return

        trigger_node = _get_redos_trigger_node(name, rule)

        # Both trigger and contrast scope are needed here.
        with scope.trigger_scope(), scope.contrast_scope():
            # we cannot use trigger_policy.apply here due to the instance_method
            # logic it uses to remove self_obj from args. For the redos action,
            # specifically for re.Pattern.method nodes, we NEED the self_obj
            # to be in the args at this time.
            source = trigger_node.get_matching_sources(None, result, args, kwargs)[0]
            cs__apply_trigger(
                context,
                rule,
                trigger_node,
                source,
                None,
                result,
                None,
                args,
                kwargs,
            )


def _get_redos_trigger_node(trigger_name, rule):
    trigger_loc = "re"
    if "Pattern" in trigger_name:
        trigger_loc = PATTERN_CLASS

    func_name = trigger_name.split(".")[-1]
    trigger_nodes = rule.find_trigger_nodes(trigger_loc, func_name)

    return trigger_nodes[0]


def build_sub_hook(original_func, policy_node):
    policy_node = get_propagation_node(policy_node)

    def sub_hook(wrapped, instance, args, kwargs):
        """
        Hook for re.sub and re.subn used for propagation in assess

        The following explains why we can't simply patch these methods using
        policy.

        It is possible for the repl argument to be a callable. In this case, the
        callable is passed a Match object, and it returns the string to be used for
        the replacement. In order to correctly propagate the substitution
        operation, we need to keep track of the results of calling the replacement
        function.

        It might seem like we should just call the replacement function again
        during our propagation action. But this is not practicable for several
        reasons:

          1. We're in scope at the time, so any propagation that needs to occur
             within the replacement callable itself will be missed.
          2. Related to above, but methods of Match do not return the same object
             even when called multiple times with the same arguments, so we would
             not be tracking the strings that actually get used in the substitution
             result.
          3. There's no guarantee that the replacement function does not cause any
             side effects or rely on any state in application code. We definitely
             don't want to mess around with this.

        The solution is to wrap the replacement callable with our own function that
        records the results of each call. We then pass our wrapped callable to the
        original function, and we pass the accumulated results to the propagator.
        This has the additional benefit of allowing us to wrap the match object
        that is passed to the repl function with our proxied object so that we
        propagate any calls that are made within this function if necessary.
        """
        # Get the non-propagation case out of the way here
        context = contrast.REQUEST_CONTEXT.get()
        if context is None or not context.propagate_assess or context.stop_propagation:
            return wrapped(*args, **kwargs)
        context.propagated()

        packed_args = pack_self(instance, args)

        try:
            repl = packed_args[1]
            new_repl, repl_results = wrap_repl(repl) if callable(repl) else (repl, None)
            new_args = tuple(packed_args[:1]) + (new_repl,) + tuple(packed_args[2:])
        except Exception:
            # This indicates that the original caller passed garbage, so call the original
            # function and let the error propagate back up to where they can clean up their
            # own mess.
            return wrapped(*args, **kwargs)

        # Account for the fact that the call to wrapped never takes a self
        call_args_idx = 1 if instance is not None else 0
        retval = wrapped(*new_args[call_args_idx:], **kwargs)

        _trigger_redos(policy_node.name, retval, packed_args, kwargs)
        _analyze_sub(policy_node, retval, repl_results, packed_args, kwargs, new_args)

        return retval

    return wrap_and_watermark(original_func, sub_hook)


def build_re_assess_hook(original_func, patch_policy):
    """Builds patch that analyzes for both redos trigger and regex propagation"""

    def assess_hook(wrapped, instance, args, kwargs):
        result = wrapped(*args, **kwargs)
        args = pack_self(instance, args)
        _trigger_redos(patch_policy.name, result, args, kwargs)
        analyze_policy(patch_policy.name, result, args, kwargs)
        return result

    return wrap_and_watermark(original_func, assess_hook)


def build_re_pattern_redos_hook(original_func, _):
    """
    Builds patch for re.Pattern methods that performs analysis for redos trigger only
    """

    method_name = original_func.__name__
    full_name = "re.Pattern." + method_name

    def redos_hook(wrapped, instance, args, kwargs):
        retval = wrapped(*args, **kwargs)
        _trigger_redos(full_name, retval, pack_self(instance, args), kwargs)
        return retval

    return wrap_and_watermark(original_func, redos_hook)


def patch_re(re_module):
    # The re.Pattern and re.Match classes are not directly accessible in all versions
    # of Python, so we do this somewhat hacky workaround to get a reference to them.
    pattern_cls = re_module.compile("").__class__
    match_cls = re_module.match("", "").__class__

    build_and_apply_patch(re_module, "sub", build_sub_hook)
    build_and_apply_patch(re_module, "subn", build_sub_hook)

    build_and_apply_patch(pattern_cls, "sub", build_sub_hook, owner_name=PATTERN_CLASS)
    build_and_apply_patch(pattern_cls, "subn", build_sub_hook, owner_name=PATTERN_CLASS)
    build_and_apply_patch(
        pattern_cls,
        "split",
        build_re_assess_hook,
        owner_name=PATTERN_CLASS,
    )
    build_and_apply_patch(
        pattern_cls,
        "findall",
        build_re_assess_hook,
        owner_name=PATTERN_CLASS,
    )

    build_and_apply_patch(
        pattern_cls,
        "match",
        build_re_pattern_redos_hook,
        owner_name=PATTERN_CLASS,
    )
    build_and_apply_patch(
        pattern_cls,
        "search",
        build_re_pattern_redos_hook,
        owner_name=PATTERN_CLASS,
    )
    build_and_apply_patch(
        pattern_cls, "finditer", build_re_pattern_redos_hook, owner_name=PATTERN_CLASS
    )

    build_and_apply_patch(
        pattern_cls,
        "fullmatch",
        build_re_pattern_redos_hook,
        owner_name=PATTERN_CLASS,
    )

    build_and_apply_patch(
        match_cls,
        "group",
        build_group_hook,
        (regex_propagator.propagate_group,),
        owner_name=MATCH_CLASS,
    )
    build_and_apply_patch(
        match_cls,
        "groups",
        build_group_hook,
        (regex_propagator.propagate_groups,),
        owner_name=MATCH_CLASS,
    )
    build_and_apply_patch(
        match_cls,
        "groupdict",
        build_group_hook,
        (regex_propagator.propagate_groupdict,),
        owner_name=MATCH_CLASS,
    )


def register_patches():
    register_module_patcher(patch_re, "re")


def reverse_patches():
    unregister_module_patcher("re")
    re_module = sys.modules.get("re")
    if not re_module:
        return

    pattern_cls = re_module.compile("").__class__
    match_cls = re_module.match("", "").__class__

    patch_manager.reverse_patches_by_owner(re_module)
    patch_manager.reverse_patches_by_owner(pattern_cls)
    patch_manager.reverse_patches_by_owner(match_cls)
