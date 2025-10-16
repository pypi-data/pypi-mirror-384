from collections.abc import Collection
from typing import Any

import click


class CommaSeparated(click.ParamType):
    name = 'comma-separated'

    def __init__(self, subtype: type[Any] = str, container: type[Collection[Any]] = list):
        self.subtype = subtype
        self.container = container

    def convert(self, value, param, ctx):
        if isinstance(value, self.container) and all(
            isinstance(item, self.subtype) for item in value
        ):
            return value

        try:
            return self.container(self.subtype(item.strip()) for item in value.split(','))

        except Exception:
            self.fail(
                f'Could not parse {value!r} as comma-separated {self.subtype.__name__}', param, ctx
            )
