"""Unit tests for the argmerge._json::parse_json() function."""

import json

import pytest

from argmerge.json import parse_json
from tests.utils import no_error


@pytest.mark.parametrize(
    "threshold_kwargs,change_ledger,fpath_json,debug,expected_kwargs,expected_ledger,context",
    [
        # file does not exist
        pytest.param(
            {},
            {},
            "missing_config.json",
            False,
            None,
            None,
            pytest.raises(FileNotFoundError),
        ),
        # wrong filepath extension -> ValueError
        pytest.param(
            {},
            {},
            "fpath_config.cfg",
            False,
            None,
            None,
            pytest.raises(ValueError),
        ),
        # broken JSON -> error
        pytest.param(
            {},
            {},
            "tests/json/bad_config.json",
            False,
            None,
            None,
            pytest.raises(json.JSONDecodeError),
        ),
        # working example
        # debug true
        pytest.param(
            {},
            {},
            "tests/json/good_config.json",
            True,
            {"first": 1, "second": {"third": 3, "d": 4}},
            {
                "first": {"label": "JSON (tests/json/good_config.json)", "rank": 10},
                "second": {"label": "JSON (tests/json/good_config.json)", "rank": 10},
            },
            no_error,
        ),
        # debug false
        pytest.param(
            {"first": 7, "third": 9},
            {
                "first": {"label": "JSON (other.json)", "rank": 10},
                "third": {"label": "JSON (other.json)", "rank": 10},
            },
            "tests/json/good_config.json",
            True,
            {"first": 1, "second": {"third": 3, "d": 4}, "third": 9},
            {
                "first": {"label": "JSON (tests/json/good_config.json)", "rank": 10},
                "second": {"label": "JSON (tests/json/good_config.json)", "rank": 10},
                "third": {"label": "JSON (other.json)", "rank": 10},
            },
            no_error,
        ),
    ],
)
def test_parse_json(
    threshold_kwargs,
    change_ledger,
    fpath_json,
    debug,
    expected_kwargs,  # output[0]
    expected_ledger,  # output[1]
    context,  # whether or not is an error
):
    with context:
        threshold_kwargs_, change_ledger_ = parse_json(
            threshold_kwargs, change_ledger, fpath_json, debug=debug
        )
        assert threshold_kwargs_ == expected_kwargs
        assert change_ledger_ == expected_ledger
