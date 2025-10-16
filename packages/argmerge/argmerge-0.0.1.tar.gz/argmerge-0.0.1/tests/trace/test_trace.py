import pytest

from argmerge.trace import _log_trace, _write_trace, trace_arg_lineage
from tests.utils import no_error


@pytest.mark.parametrize(
    "message,level,context",
    [
        ("Hello", "INFO", no_error),
        ("Bad level", "BAD", pytest.raises(ValueError)),
        ("WORSE LEVEL", -1, pytest.raises(TypeError)),
    ],
)
def test_write_trace(message, level, context):
    with context:
        _write_trace(message=message, level=level)


def fake_function(first: int, second: str, third: float = 0.0):
    pass


@pytest.mark.parametrize(
    "f,change_ledger,level,context",
    [
        (fake_function, {}, "INFO", no_error),
        (
            fake_function,
            {"third": {"label": "Python Function default", "rank": 0}},
            "INFO",
            no_error,
        ),
    ],
)
def test_trace_arg_lineage(f, change_ledger, level, context):
    with context:
        trace_arg_lineage(f, change_ledger, level)


@pytest.mark.parametrize("ledger,level,context", [({}, "INFO", no_error)])
def test_log_trace(ledger, level, context):
    with context:
        _log_trace(ledger, level)
