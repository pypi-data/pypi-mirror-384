from __future__ import annotations

import datetime

from clearskies.di.injectable import Injectable


class Now(Injectable):
    def __init__(self, cache: bool = False):
        self.cache = cache

    def __get__(self, instance, parent) -> datetime.datetime:
        if instance is None:
            return self  # type: ignore
        return self._di.build_from_name("now", cache=self.cache)
