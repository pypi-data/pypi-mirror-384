import pytest

from argmerge.cli import CLI_PATTERN, parse_cli
from tests.utils import no_error

test_cases = [
    (
        ["", "--config=config.txt", "--debug=True"],
        {},
        {},
        CLI_PATTERN,
        True,
        {"config": "config.txt", "debug": "True"},
        {"config": {"label": "CLI", "rank": 40}, "debug": {"label": "CLI", "rank": 40}},
        no_error,
    ),
    (
        ["", "--config", "config.txt", "--debug=True"],
        {},
        {},
        r"--([A-Za-z\_\-]+)\=([0-9A-Za-z\_\-\.]+)",
        True,
        {"debug": "True"},
        {"debug": {"label": "CLI", "rank": 40}},
        no_error,
    ),
]


@pytest.mark.parametrize(
    "cli_args,threshold_kwargs,change_ledger,cli_pattern,"
    "debug,expected_kwargs,expected_ledger,context",
    test_cases,
)
def test_cli_parsing(
    monkeypatch,
    cli_args,
    threshold_kwargs,
    change_ledger,
    cli_pattern,
    debug,
    expected_kwargs,
    expected_ledger,
    context,
):
    monkeypatch.setattr("sys.argv", cli_args)

    with context:
        threshold_kwargs_, change_ledger_ = parse_cli(
            threshold_kwargs, change_ledger, cli_pattern, debug
        )

        assert threshold_kwargs_ == expected_kwargs
        assert change_ledger_ == expected_ledger
