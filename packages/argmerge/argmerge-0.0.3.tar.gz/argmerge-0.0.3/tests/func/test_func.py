"""Unit tests for the argmerge._func::{parse_func, parse_func_runtime} functions."""

import pytest

from argmerge.func import parse_func, parse_func_runtime
from tests.utils import no_error


# [parse_func]
def no_default_params(first: int, second: str, third: float):
    pass


def mixed_params(first: int, second: str, third: float = 0.0):
    pass


def all_default_params(first: int = 7, second: str = "", third: float = 0.0):
    pass


@pytest.mark.parametrize(
    "threshold_kwargs, change_ledger,function, debug,expected_kwargs, expected_ledger, context",
    [
        # if not a callable is passed
        (None, None, None, False, None, None, pytest.raises(TypeError)),
        # if no parameters with defaults are passed
        ({}, {}, no_default_params, False, {}, {}, no_error),
        # if mix of default/not default params are passed
        (
            {},
            {},
            mixed_params,
            True,
            {"third": 0.0},
            {"third": {"label": "Python Function Default", "rank": 0}},
            no_error,
        ),
        # if all functions have defaults
        (
            {},
            {},
            all_default_params,
            True,
            {"first": 7, "second": "", "third": 0.0},
            {
                "third": {"label": "Python Function Default", "rank": 0},
                "second": {"label": "Python Function Default", "rank": 0},
                "first": {"label": "Python Function Default", "rank": 0},
            },
            no_error,
        ),
    ],
)
def test_parse_func(
    function,
    debug,
    threshold_kwargs,
    change_ledger,
    expected_kwargs,
    expected_ledger,
    context,
):
    with context:
        _expected_kwargs, _expected_ledger = parse_func(
            threshold_kwargs, change_ledger, function, debug
        )
        assert expected_kwargs == _expected_kwargs
        assert expected_ledger == _expected_ledger


# [parse_func_runtime]
@pytest.mark.parametrize(
    "threshold_kwargs,change_ledger,func_kwargs,debug,expected_kwargs,expected_ledger,context,",
    [
        # no previous changes
        (
            {},
            {},
            {"first": 1},
            False,
            {"first": 1},
            {"first": {"label": "Developer-provided", "rank": 100}},
            no_error,
        ),
        # one previous change
        (
            {"first": 3},
            {"first": {"label": "Python Function Default", "rank": 0}},
            {"first": 1},
            False,
            {"first": 1},
            {"first": {"label": "Developer-provided", "rank": 100}},
            no_error,
        ),
        # many previous changes from many levels
        (
            {"first": 1, "second": "", "third": 0.0},
            {
                "first": {"label": "Python Function Default", "rank": 0},
                "second": {"label": "Environment Variable", "rank": 30},
                "third": {"label": "CLI", "rank": 40},
            },
            {"first": 99, "second": "Ken Thompson", "third": -0.8},
            True,
            {"first": 99, "second": "Ken Thompson", "third": -0.8},
            {
                "first": {"label": "Developer-provided", "rank": 100},
                "second": {"label": "Developer-provided", "rank": 100},
                "third": {"label": "Developer-provided", "rank": 100},
            },
            no_error,
        ),
    ],
)
def test_parse_func_runtime(
    threshold_kwargs,
    change_ledger,
    func_kwargs,
    debug,
    expected_kwargs,
    expected_ledger,
    context,
):
    with context:
        _expected_kwargs, _expected_ledger = parse_func_runtime(
            threshold_kwargs, change_ledger, func_kwargs, debug
        )
        assert expected_kwargs == _expected_kwargs
        assert expected_ledger == _expected_ledger
