"""Module to write the source of each function keyword argument for the developer

Example:

    $ uv run main.py  # trace_level=DEBUG set in the program
    2025-10-14 16:15:33.466 | DEBUG    | argmerge.trace:_write_trace:50 -
    Parameter Name  | Source
    =======================================
    third   | Python Function default
    fourth  | Python Function default
    fifth   | Python Function default
    first   | developer-provided
    second  | developer-provided
    =======================================
"""

import sys
from inspect import signature
from typing import Callable

from loguru import logger as LOGGER

LOG_LEVELS = ("critical", "warning", "success", "info", "debug")


def _write_trace(message: str, level: str):
    """Write the trace message out to the specified log level.

    args:
        message (str): The debugging message for the developer.
        level (str): The `loguru` log level to set.

    raises:
        TypeError: `level` must be a string.
        ValueError: `level` must be in one of the default loguru logger levels:
            `("critical", "warning", "success", "info", "debug")`
    """
    if isinstance(level, str):
        _level = level.lower()

    else:
        raise TypeError(f"Log level '{level}' ({type(level)}) is not a string.")

    if _level not in LOG_LEVELS:
        raise ValueError(
            f"Log level '{_level}' not in basic loguru log levels: '{LOG_LEVELS}''."
        )

    _trace_logger: int = LOGGER.add(sys.stderr, level=level.upper())

    getattr(LOGGER, _level.lower())(message)

    LOGGER.remove(_trace_logger)


def _log_trace(ledger: dict[str, dict[str, str | int]], level: str = ""):
    """Compose a developer-friendly report of each kwarg's source form the ledger.

    First, sort the keys by their ranks. Ranks are sorted in ascending order such that
    the highest ranked sources (Developer-Provided, etc) will be seen first. Then sort
    the labels by that same order. Next, we will dynamically produce the report. We
    will find the kwarg and source each with the longest length. Then, left-justify
    (ljust) each kwarg and source to fill the space. Repeat for each kwarg-source pair.
    We then set the heading such that the '=' characters "hang" over the report,
    visually grouping them.

    Args:
        ledger (dict[str, dict[str, str  |  int]]): The change ledger that describes
            each kwarg's highest-ranked source.
        level (str, optional): A `loguru` logging level. Defaults to "", which means
            'DEBUG' will be set.
    """

    if len(ledger) == 0:
        LOGGER.warning("Change ledger is empty, will not write out!")

    else:
        # split the ranks from the labels
        ranks: dict[str, int] = {k: int(v["rank"]) for k, v in ledger.items()}
        labels: dict[str, str] = {k: str(v["label"]) for k, v in ledger.items()}

        # First, sort the keys by their ranks.
        sorted_keys = [x for x, _ in sorted(ranks.items(), key=lambda x: x[1])]
        sorted_labels = {k: labels[k] for k in sorted_keys}

        # calculate the longest kwarg name and source name
        _key_spacing: int = max(list(map(len, sorted_labels.keys())))
        _value_spacing: int = max(list(map(len, sorted_labels.values())))

        # left-justify
        _pre_join_spacing = {
            k.ljust(_key_spacing, " "): v.ljust(_value_spacing, " ")
            for k, v in sorted_labels.items()
        }

        # stringified, left-justified kwargs and sources
        _params = [f"{k}\t| {v}" for k, v in _pre_join_spacing.items()]

        # set up the heading
        # heading will extend over the params
        _heading_spacing: int = max(map(len, _params)) + 7

        _heading_param = "Parameter Name".ljust(_key_spacing)
        _heading_loc = "Source".ljust(_value_spacing)

        # construct the full heading
        _heading = f"{_heading_param}\t| {_heading_loc}"

        _body = "\n".join(_params)

        # combine the heading with the body
        msg = (
            f"\n{_heading}\n{'=' * _heading_spacing}\n{_body}\n{'=' * _heading_spacing}"
        )

        # log it to the appropriate level
        _write_trace(message=msg, level=level)


def trace_arg_lineage(
    f: Callable,
    change_ledger: dict[str, dict[str, str | int]],
    level: str = "",
):
    """Determine where each argument in the function came from.

    Only include arguments that exist in the function header. If a function accepts
    **kwargs and an irrelevant keyword is provided - discard it.

    args:
        f (callable):
        change_ledger (dict): The final dictionary detailing where every argument
            is set - defaults, files, environment variables, CLI arguments, etc.
    """
    sig = signature(f)
    _changed = {k: v for k, v in change_ledger.items() if k in sig.parameters}

    _log_trace(ledger=_changed, level=level)
