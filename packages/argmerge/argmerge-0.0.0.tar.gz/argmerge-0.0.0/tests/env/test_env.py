"""Unit tests for the argmerge._func::{parse_func, update_from_function} functions."""

import re

import pytest

from argmerge.env import ENV_PREFIX, parse_env
from tests.utils import no_error

# string pattern
# regex pattern
# neither string/regex pattern


@pytest.mark.parametrize(
    "env_mapping,threshold_kwargs,change_ledger,env_prefix,debug,expected_kwargs,"
    "expected_ledger,context,",
    [
        # No Environment Variables - no change
        (
            {},
            {"first": 1},
            {"first": {"label": "Python Function default", "rank": 0}},
            "THRESH",
            False,
            {"first": 1},
            {"first": {"label": "Python Function default", "rank": 0}},
            no_error,
        ),
        # No relevant Environment Variables
        (
            {"COLORTERM": "truecolor"},
            {"first": 1},
            {"first": {"label": "Python Function default", "rank": 0}},
            "THRESH",
            False,
            {"first": 1},
            {"first": {"label": "Python Function default", "rank": 0}},
            no_error,
        ),
        # Two Environment Variables - extractable values
        (
            {"THRESH_FIRST": "99", "THRESH_SECOND": "2"},
            {"first": 1},
            {"first": {"label": "Python Function default", "rank": 0}},
            "THRESH",
            True,
            {"first": 99, "second": 2},
            {
                "first": {"label": "Environment Variable", "rank": 30},
                "second": {"label": "Environment Variable", "rank": 30},
            },
            no_error,
        ),
        # Three environment variables, one is a string
        (
            {
                "THRESH_FIRST": "99",
                "THRESH_SECOND": "2.0",
                "THRESH_THIRD": "laugh",
            },
            {"first": 1},
            {"first": {"label": "Python Function default", "rank": 0}},
            "THRESH",
            True,
            {"first": 99, "second": 2, "third": "laugh"},
            {
                "first": {"label": "Environment Variable", "rank": 30},
                "second": {"label": "Environment Variable", "rank": 30},
                "third": {"label": "Environment Variable", "rank": 30},
            },
            no_error,
        ),
        # Use the environment variable to retrieve the prefix, PYTHRESH
        (
            {
                "NOT_RELEVANT_FIRST": "99",
                "THRESH_SECOND": "2.0",
                "THRESH_THIRD": "laugh",
            },
            {"first": 1},
            {"first": {"label": "Python Function default", "rank": 0}},
            ENV_PREFIX,
            True,
            {"first": 1, "second": 2.0, "third": "laugh"},
            {
                "first": {"label": "Python Function default", "rank": 0},
                "second": {"label": "Environment Variable", "rank": 30},
                "third": {"label": "Environment Variable", "rank": 30},
            },
            no_error,
        ),
        # Do NOT Provide a capture group in the regex pattern
        # this will skip THRESH_B an THRESH_C
        # The proper Regex is r'^THRESH.([A-Z_-]+)$'
        (
            {
                "NOT_RELEVANT_FIRST": "99",
                "THRESH_SECOND": "2.0",
                "THRESH_THIRD": "laugh",
            },
            {"first": 1},
            {"first": {"label": "Python Function default", "rank": 0}},
            re.compile("^THRESH.[A-Z_-]+"),
            True,
            {"first": 1},
            {
                "first": {"label": "Python Function default", "rank": 0},
            },
            no_error,
        ),
        (
            {
                "NOT_RELEVANT_FIRST": "99",
                "THRESH_SECOND": "2.0",
                "THRESH_THIRD": "laugh",
            },
            {"first": 1},
            {"first": {"label": "Python Function default", "rank": 0}},
            77,
            True,
            {"first": 1, "second": 2.0, "third": "laugh"},
            {
                "first": {"label": "Python Function default", "rank": 0},
                "second": {"label": "Environment Variable", "rank": 30},
                "third": {"label": "Environment Variable", "rank": 30},
            },
            pytest.raises(ValueError),
        ),
    ],
)
def test_parse_env(
    monkeypatch,
    env_mapping,
    threshold_kwargs,
    change_ledger,
    env_prefix,
    debug,
    expected_kwargs,
    expected_ledger,
    context,
):
    with monkeypatch.context() as m:
        for env_var_name, env_var_value in env_mapping.items():
            m.setenv(env_var_name, env_var_value)

        with context:
            threshold_kwargs_, change_ledger_ = parse_env(
                threshold_kwargs, change_ledger, env_prefix, debug
            )
            assert threshold_kwargs_ == expected_kwargs
            assert change_ledger_ == expected_ledger
