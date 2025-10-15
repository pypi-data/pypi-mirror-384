# Copyright © 2025 Contrast Security, Inc.
# See https://www.contrastsecurity.com/enduser-terms-0317a for more details.
from __future__ import annotations
from collections.abc import Sequence
from typing import Literal, Union
from contrast.agent.policy import constants
from contrast.agent.assess.assess_exceptions import ContrastAssessException
from contrast_fireball import AssessEventAction, AssessEventType

UNDERSCORE = "_"
COMMA = ","
COLON = ":"

Location = Union[
    Literal["OBJ"],
    int,  # args index
    str,  # kwargs key
    Literal["RETURN"],
]
# variables can't be used within Literal, or the Union becomes
# a (variable) not a (type). So we have to duplicate the strings.
# This is an extra check to ensure that the strings are the same.
assert constants.OBJECT == "OBJ"
assert constants.RETURN == "RETURN"


class PolicyNode:
    def __init__(
        self,
        module="",
        class_name="",
        instance_method=True,
        method_name="",
        source="",
        target="",
        tags: Sequence[str] | None = None,
        policy_patch=True,
    ):
        self.module = module
        self.class_name = class_name or ""

        # If no class_name is given, it indicates that this node corresponds to a
        # standalone function, not a method. This means that instance_method is always
        # False. Otherwise we use the given value of instance_method. However, the
        # default for this argument will be True if not given for all policy nodes,
        # which means that only methods that are **not** instance methods must provide
        # it explicitly. This value is used to determine whether or not the first
        # positional argument should be treated as "self" or not by our policy
        # machinery
        self.instance_method = instance_method if class_name else False

        self.method_name = method_name

        self.sources = self.parse_source_or_target(source)
        self.targets = self.parse_source_or_target(target)

        self.ts_valid_source = self.ts_represent(source)
        self.ts_valid_target = self.ts_represent(target)

        self.tags = set()

        if tags:
            self.tags.update(tags)

        # This attribute indicates whether a given policy node corresponds to a patch
        # that should be applied by policy. It defaults to True. However, many of our
        # policy nodes are **not** patched by policy but instead are patched in a
        # different way. For example, nearly all of our string propagators are applied
        # as C hooks. In these cases we still use the policy node for reporting
        # purposes, but we don't want a policy patch.
        self.policy_patch = policy_patch

        self.skip_stacktrace = False
        self.properties: dict[str, str] = {}

    @property
    def name(self) -> str:
        """
        Fully specified unique name for this node

        Includes module name, class name (if applicable) and method name
        """
        return f"{self.location}.{self.method_name}"

    @property
    def location(self) -> str:
        """
        Property indicating the fully specified location of the patched method/function

        For a method of a class:
            <module_path>.<class_name>.<method_name>

        For a function:
            <module_path>.<function_name>
        """
        return f"{self.module}{'.' + self.class_name if self.class_name else ''}"

    def add_property(self, name: str, value: str):
        if not name or not value:
            return

        self.properties[name] = value

    @property
    def node_class(self) -> str:
        return self.__class__.__name__.replace("Node", "")

    @property
    def node_type(self) -> AssessEventType:
        return AssessEventType.METHOD

    def parse_source_or_target(self, str_rep: str) -> list[Location]:
        """
        Given a string source or target, split it into its list representation
        by splitting on ',' and appending the appropriate represntation to the list.

        :param str_rep: string representation of a source or target, such as 'ARG_0, OBJ'
        :return: list representation of source or target, [0, 'OBJ']
        """
        ret = []

        if not str_rep:
            return []

        for item in str_rep.split(COMMA):
            if item in {
                constants.OBJECT,
                constants.RETURN,
                constants.ALL_ARGS,
                constants.ALL_KWARGS,
            }:
                ret.append(item)

            # handle ARG_#
            elif item.startswith(constants.ARG + UNDERSCORE):
                arg_num = item.split(UNDERSCORE)[1]
                ret.append(int(arg_num))

            # handle KWARG:name
            elif item.startswith(constants.KWARG + COLON):
                kwarg_name = item.split(COLON)[1]
                ret.append(kwarg_name)

            else:
                return []

        return ret

    def ts_represent(self, str_rep: str) -> str:
        """
        Convert source/target from policy.json into TS-valid version.
        * ARG_# --> P#
        * ARG_0,KWARG:location --> P0,KWARG:location
            TS will ignore everything after P0; kwargs are not directly supported in TS
        * KWARG:location --> P0
            Pure kwarg functions are rare in Python but we must support them. However,
            kwargs are not directly supported in TS so for now we send a fake P0.
        * ALL_ARGS or ALL_KWARGS --> P0
            TS does not currently support sending an arbitrary number of args/kwargs for
            source/target value
        """
        if not str_rep:
            return ""
        if str_rep.startswith(
            (
                constants.KWARG,
                constants.ALL_ARGS,
                constants.ALL_KWARGS,
            )
        ):
            return "P0"

        return str_rep.replace("ARG_", "P")

    def get_matching_first_target(self, self_obj, ret, args, kwargs) -> object:
        node_target = self.targets[0]

        if node_target is None:
            return None

        if node_target == constants.ALL_ARGS:
            return args

        if node_target == constants.RETURN:
            return ret

        if node_target == constants.OBJECT:
            return self_obj

        if args and isinstance(node_target, int):
            return args[node_target]

        return kwargs.get(node_target) if kwargs else None

    def validate(self) -> None:
        if not self.module:
            raise ContrastAssessException(
                f"{self.node_class} unknown did not have a proper module. Unable to create."
            )

        if not self.method_name:
            raise ContrastAssessException(
                f"{self.node_class} did not have a proper method name. Unable to create."
            )

        self.validate_tags()

    def validate_tags(self) -> None:
        if not self.tags:
            return

        for item in self.tags:
            if not (
                item in constants.VALID_TAGS or item in constants.VALID_SOURCE_TAGS
            ):
                raise ContrastAssessException(
                    f"{self.node_class} {self.name} had an invalid tag. {item} is not a known value."
                )

    def _type_to_action(self, sources_or_targets) -> str:
        """
        Convert a list of sources or targets into a TS-valid action string.
        """
        if not sources_or_targets:
            return ""

        if len(sources_or_targets) > 1:
            return constants.ALL_KEY

        item = sources_or_targets[0]

        if item in (constants.ALL_ARGS, constants.ALL_KWARGS):
            return constants.ALL_KEY

        if item == constants.OBJECT:
            return constants.OBJECT_KEY

        # only target, not source, can be return type
        if item == constants.RETURN:
            return constants.RETURN_KEY

        return constants.ARG_OR_KWARG

    def build_action(self) -> AssessEventAction:
        """
        Convert our action, built from our source and target, into
        the TS appropriate action.

        Creation (source nodes) don't have sources (they are the source)
        Trigger (trigger nodes) don't have targets (they are the target)
        Everything else (propagation nodes) are Source2Target
        """
        if not self.sources:
            event_action = AssessEventAction.CREATION
        elif not self.targets:
            event_action = AssessEventAction.TRIGGER
        else:
            source = self._type_to_action(self.sources)
            target = self._type_to_action(self.targets)

            event_action = AssessEventAction[f"{source}2{target}"]

        return event_action

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} - {self.name}"
