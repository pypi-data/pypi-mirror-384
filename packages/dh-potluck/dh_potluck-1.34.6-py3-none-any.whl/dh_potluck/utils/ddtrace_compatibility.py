import ddtrace
from packaging.version import parse as vparse

DDTRACE_V2 = vparse(ddtrace.__version__).major == 2


if DDTRACE_V2:
    from ddtrace import patch  # type: ignore # noqa
    from ddtrace import tracer  # type: ignore # noqa
    from ddtrace.contrib.flask import unpatch  # type: ignore # noqa
    from ddtrace.filters import TraceFilter  # type: ignore # noqa
else:
    from ddtrace import patch  # type: ignore  # noqa
    from ddtrace.trace import TraceFilter, tracer  # type: ignore  # noqa

    def unpatch(*args, **kwargs):  # no-op on v3+
        pass
