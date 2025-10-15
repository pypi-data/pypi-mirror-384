# Copyright © 2025 Contrast Security, Inc.
# See https://www.contrastsecurity.com/enduser-terms-0317a for more details.
from datetime import timedelta
import contextlib


class SessionAgeRuleMixin:
    @property
    def name(self):
        return "session-timeout"

    def is_violated(self, value):
        """
        A value of 30 mins or less is considered safe

        Flask represents this value as either a timedelta or as an integer in seconds.
        All other frameworks represent it as an integer representing seconds.
        """
        if self.count_threshold_reached():
            return False
        if isinstance(value, timedelta):
            return value > timedelta(minutes=30)

        if isinstance(value, str):
            with contextlib.suppress(ValueError):
                value = int(value)

        return value is None or value > 30 * 60
